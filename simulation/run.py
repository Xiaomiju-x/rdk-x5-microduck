"""Offline FT teaching simulation. No serial, SSH, real robot or policy inference.

Model/data licensing: model/manifest.json and NOTICE.md.
Python code: Apache-2.0, RDK X5 MicroDuck project / CanNyCat.
"""
from __future__ import annotations

import argparse
from contextlib import nullcontext
import hashlib
import json
import math
from pathlib import Path
import platform
import shutil
import subprocess
import time
import xml.etree.ElementTree as ET

import mujoco
import numpy as np

HERE = Path(__file__).resolve().parent
MODEL = HERE / "model" / "ft_bare.xml"


def verify_assets():
    manifest = json.loads((MODEL.parent / "manifest.json").read_text("utf8"))
    for rel, expected in manifest["files_sha256"].items():
        path = MODEL.parent / rel
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError(f"Model asset changed: {rel}. Keep the reference intact; edit a copy for research.")
    return manifest


def build_model(suspended=False, payload=None):
    root = ET.parse(MODEL).getroot()
    root.find("compiler").set("meshdir", str(MODEL.parent / "meshes"))
    trunk = root.find(".//body[@name='trunk_base']")
    if suspended:
        trunk.remove(trunk.find("freejoint"))
        trunk.set("pos", "0 0 .21")
    if payload:
        # Optional explicit research assumption, never read from the real device.
        cfg = json.loads(Path(payload).read_text("utf8"))
        for i, part in enumerate(cfg["parts"]):
            mass = float(part["mass_kg"])
            pos = np.asarray(part["center_m"], dtype=float)
            size = np.asarray(part["full_size_m"], dtype=float)
            if (pos.shape != (3,) or size.shape != (3,) or not np.isfinite(pos).all()
                    or not np.isfinite(size).all() or not math.isfinite(mass)
                    or not 0 < mass <= 2 or np.any(size <= 0)):
                raise ValueError("Payload requires finite mass (0,2]kg, center and positive full dimensions.")
            inertia = mass / 12 * np.asarray([size[1]**2+size[2]**2,
                                              size[0]**2+size[2]**2,
                                              size[0]**2+size[1]**2])
            fmt = lambda x: " ".join(map(str, x))
            body = ET.SubElement(trunk, "body", name=f"example_payload_{i}", pos=fmt(pos))
            ET.SubElement(body, "inertial", mass=str(mass), pos="0 0 0", diaginertia=fmt(inertia))
            ET.SubElement(body, "geom", type="box", size=fmt(size/2), rgba=".2 .65 .9 .7",
                          contype="0", conaffinity="0", group="2")
    return mujoco.MjModel.from_xml_string(ET.tostring(root, encoding="unicode"))


def camera():
    cam = mujoco.MjvCamera()
    cam.lookat[:] = [0, 0, .16]
    cam.distance = .75
    cam.azimuth = 135
    cam.elevation = -12
    return cam


def labelled_frame(renderer, model, data, mode):
    from PIL import Image, ImageDraw, ImageFont
    options = mujoco.MjvOption()
    options.geomgroup[:] = 1
    renderer.update_scene(data, camera=camera(), scene_option=options)
    result = Image.fromarray(renderer.render())
    draw = ImageDraw.Draw(result)
    draw.rectangle((0, 0, result.width, 70), fill=(16, 32, 49))
    font = ImageFont.load_default(size=21)
    small = ImageFont.load_default(size=15)
    draw.text((22, 13), "FT / MuJoCo teaching reference", font=font, fill=(235, 245, 252))
    text = f"SIMULATION ONLY | {mode.upper()} | t={data.time:.2f}s | not walking validation"
    draw.text((22, 43), text, font=small, fill=(112, 222, 208))
    if mode == "joint":
        draw.text((22, result.height-35), f"Trunk fixed in air; small knee sweep | model mass {model.body_mass.sum():.3f} kg",
                  font=small, fill=(235, 245, 252))
    return np.asarray(result)


def run(args):
    manifest = verify_assets()
    suspended = args.mode == "joint"
    model = build_model(suspended, args.payload)
    data = mujoco.MjData(model)
    names = manifest["actor_names"]
    qadr = np.asarray([model.joint(n).qposadr[0] for n in names])
    home = model.qpos0[qadr].copy()
    data.ctrl[:] = home
    mujoco.mj_forward(model, data)
    root_id = model.body("trunk_base").id
    initial_com = data.subtree_com[root_id].copy()
    mins, maxs = data.qpos[qadr].copy(), data.qpos[qadr].copy()
    max_error, max_tilt, contacts_peak, completed = 0., 0., int(data.ncon), 0
    steps = int(round(args.seconds / model.opt.timestep)) if args.mode != "inspect" else 0
    renderer = mujoco.Renderer(model, height=720, width=960) if args.image or args.video else None
    writer = None
    if args.video:
        executable = shutil.which(args.ffmpeg) if args.ffmpeg else shutil.which("ffmpeg")
        if not executable:
            raise ValueError("--video requires FFmpeg on PATH or --ffmpeg /path/to/ffmpeg; JSON/image do not.")
        Path(args.video).parent.mkdir(parents=True, exist_ok=True)
        writer = subprocess.Popen([executable, "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo",
             "-pixel_format", "rgb24", "-video_size", "960x720", "-framerate", "25", "-i", "-", "-an",
             "-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(args.video)],
             stdin=subprocess.PIPE)
    viewer_context = nullcontext(None)
    if args.viewer:
        from mujoco import viewer as mjviewer
        viewer_context = mjviewer.launch_passive(model, data)
    max_clip = 0.
    try:
        with viewer_context as viewer:
            if viewer:
                with viewer.lock():
                    c = camera()
                    viewer.opt.geomgroup[:] = 1
                    viewer.cam.lookat[:] = c.lookat
                    viewer.cam.distance, viewer.cam.azimuth, viewer.cam.elevation = c.distance, c.azimuth, c.elevation
            for step in range(steps):
                clock = time.monotonic()
                target = home.copy()
                if suspended:
                    # A smooth single cycle returning to HOME. It is not D replay or a gait.
                    phase = step / max(1, steps-1)
                    pulse = math.sin(2*math.pi*phase) * math.sin(math.pi*phase)**2 * math.radians(5)
                    target[names.index("left_knee")] += pulse
                    target[names.index("right_knee")] -= pulse
                clipped = np.clip(target, model.actuator_ctrlrange[:, 0], model.actuator_ctrlrange[:, 1])
                max_clip = max(max_clip, float(np.max(np.abs(clipped-target))))
                data.ctrl[:] = clipped
                mujoco.mj_step(model, data)
                if not np.isfinite(data.qpos).all() or not np.isfinite(data.qvel).all():
                    raise RuntimeError("Non-finite physics state")
                completed += 1
                max_error = max(max_error, float(np.max(np.abs(data.qpos[qadr]-clipped))))
                mins = np.minimum(mins, data.qpos[qadr]); maxs = np.maximum(maxs, data.qpos[qadr])
                max_tilt = max(max_tilt, math.degrees(math.acos(np.clip(data.xmat[root_id].reshape(3,3)[2,2], -1, 1))))
                contacts_peak = max(contacts_peak, int(data.ncon))
                if writer and step % 8 == 0:
                    writer.stdin.write(labelled_frame(renderer, model, data, args.mode).tobytes())
                if viewer:
                    if not viewer.is_running():
                        break
                    viewer.sync()
                    time.sleep(max(0, model.opt.timestep-(time.monotonic()-clock)))
            if args.image:
                from PIL import Image
                Path(args.image).parent.mkdir(parents=True, exist_ok=True)
                Image.fromarray(labelled_frame(renderer, model, data, args.mode)).save(args.image)
    finally:
        if writer:
            writer.stdin.close()
            if writer.wait(timeout=30):
                raise RuntimeError("FFmpeg did not finish successfully")
        if renderer:
            renderer.close()
    result = {
        "scope": "OFFLINE_FT_TEACHING_SIMULATION_NOT_HARDWARE_OR_WALKING_ACCEPTANCE",
        "mode": args.mode, "trunk_fixed": suspended, "hardware_io": False,
        "complete": completed == steps, "steps": completed, "simulation_seconds": round(float(data.time),6),
        "platform": platform.system(), "python": platform.python_version(),
        "mujoco": mujoco.__version__, "numpy": np.__version__,
        "model_sha256": hashlib.sha256(MODEL.read_bytes()).hexdigest(),
        "model_manifest_sha256": hashlib.sha256((MODEL.parent/"manifest.json").read_bytes()).hexdigest(),
        "payload_sha256": hashlib.sha256(Path(args.payload).read_bytes()).hexdigest() if args.payload else None,
        "total_mass_kg": round(float(model.body_mass.sum()),9), "joint_count": model.njnt-(0 if suspended else 1),
        "actuator_count": model.nu, "timestep_s": float(model.opt.timestep),
        "payload_added": bool(args.payload), "initial_com_world_m": initial_com.tolist(),
        "final_com_world_m": data.subtree_com[root_id].tolist(),
        "max_tilt_deg": max_tilt, "peak_contact_count": contacts_peak,
        "max_target_tracking_error_deg": math.degrees(max_error), "target_clip_rad": max_clip,
        "joint_motion_range_deg": {name:float(v) for name,v in zip(names, np.degrees(maxs-mins))},
        "warning_counts": [int(w.number) for w in data.warning],
        "interpretation": "Finite integration and reported motion only; no learned policy, real load, voltage dynamics or calibrated START."
    }
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(json.dumps(result, indent=2)+"\n", encoding="utf8")
    print(json.dumps(result, indent=2))
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=["inspect", "hold", "joint"], help="hold: free base; joint: fixed trunk in air")
    p.add_argument("--seconds", type=float, default=2.)
    p.add_argument("--payload", help="Explicit research payload JSON; omitted = bare body")
    p.add_argument("--output", help="JSON report path")
    p.add_argument("--image", help="PNG snapshot path; requires OpenGL")
    p.add_argument("--video", help="MP4 path; requires OpenGL and FFmpeg")
    p.add_argument("--ffmpeg", help="FFmpeg executable (or put ffmpeg on PATH)")
    p.add_argument("--viewer", action="store_true", help="Open interactive window; no serial or network")
    args = p.parse_args()
    if not math.isfinite(args.seconds) or not 0 < args.seconds <= 60:
        p.error("--seconds must be finite and in (0,60]")
    run(args)


if __name__ == "__main__":
    main()
