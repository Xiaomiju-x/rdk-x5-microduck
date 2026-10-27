"""Read-only JY901S diagnostics, independent of the servo port and gait.

The reported body pitch uses the same gravity conversion as runtime.py.
This tool does not estimate a mounting rotation or set a verification flag.
"""
import math
import time

import numpy as np

from imu import ImuTrace


def validate_imu_config(cfg):
    port = cfg.get('imu_port')
    if not isinstance(port, str) or not port or port.startswith('SET_'):
        raise ValueError('Set imu_port to the actual IMU serial device')
    if cfg.get('imu_baud') != 115200:
        raise ValueError('This reference reads JY901S at 115200 baud; it never changes the device baud')
    rotation = np.asarray(cfg.get('body_from_sensor_rotation'), dtype=float)
    if (rotation.shape != (3, 3) or not np.isfinite(rotation).all()
            or not np.allclose(rotation.T @ rotation, np.eye(3), atol=1e-6)
            or not np.isclose(np.linalg.det(rotation), 1, atol=1e-6)):
        raise ValueError('body_from_sensor_rotation must be a finite proper 3x3 rotation')
    return rotation


def body_values(angles, gyro, rotation):
    r, p, _ = np.radians(np.asarray(angles, dtype=np.float32)).astype(float)
    gravity = np.array([math.sin(p), -math.sin(r)*math.cos(p), -math.cos(r)*math.cos(p)], dtype=np.float32)
    body_gravity = rotation @ gravity
    return {
        'body_gravity_unit': body_gravity.tolist(),
        'body_gyro_dps': (rotation @ np.asarray(gyro, dtype=float)).tolist(),
        'body_pitch_deg': float(np.degrees(np.arctan2(body_gravity[0], np.hypot(body_gravity[1], body_gravity[2])))),
        'body_roll_deg': float(np.degrees(np.arctan2(-body_gravity[1], -body_gravity[2]))),
    }


def packet_stats(records, kind, began, ended):
    stamps = sorted(r['mono_s'] for r in records if r['kind'] == kind and began <= r['mono_s'] <= ended)
    elapsed = ended-began
    return {
        'packets': len(stamps),
        'host_observed_hz': len(stamps)/elapsed if elapsed > 0 else 0.,
        'max_host_gap_ms': max((b-a for a, b in zip(stamps, stamps[1:])), default=0.)*1000,
    }


def inspect_imu(cfg, seconds=5., progress=lambda _: None, cancel=lambda: None,
                trace_factory=ImuTrace, clock=time):
    rotation = validate_imu_config(cfg)
    if type(seconds) not in (float, int) or not math.isfinite(seconds) or not 1 <= seconds <= 60:
        raise ValueError('seconds must be a finite number between 1 and 60')
    # No servo module, serial write, enable, configuration update or file write.
    trace = trace_factory(cfg['imu_port'], cfg['imu_baud'])
    samples = []
    baseline = None
    began = None
    status = None
    try:
        trace.start()
        began = clock.monotonic()
        while clock.monotonic()-began < seconds:
            cancel()
            snapshot = trace.snapshot()
            gyro = trace.latest.get(0x52)
            if not snapshot or snapshot.get('error') or not gyro:
                raise RuntimeError('Missing valid angle/gyro data')
            gyro_age = (clock.monotonic()-gyro['mono_s'])*1000
            if snapshot['host_age_ms'] > 150 or gyro_age > 150:
                raise RuntimeError('IMU stream stale (angle or gyro older than 150 ms)')
            values = body_values(snapshot['sensor_angles_deg'], gyro['sensor_gyro_dps'], rotation)
            if baseline is None:
                baseline = values['body_pitch_deg']
            row = dict(t_s=clock.monotonic()-began,
                       sensor_angles_deg=snapshot['sensor_angles_deg'],
                       sensor_gyro_dps=gyro['sensor_gyro_dps'],
                       angle_age_ms=snapshot['host_age_ms'], gyro_age_ms=gyro_age,
                       pitch_delta_deg=values['body_pitch_deg']-baseline, **values)
            samples.append(row)
            progress(dict(action='imu-check', **row))
            clock.sleep(min(.25, max(0., seconds-(clock.monotonic()-began))))
        ended = clock.monotonic()
    finally:
        status = trace.stop()
    if status.get('error') or not status.get('thread_stopped', True):
        raise RuntimeError('IMU reader did not finish cleanly: '+str(status.get('error')))
    records = status['records']
    return dict(action='imu-check', status='READ_ONLY_CAPTURE_COMPLETE_DIRECTION_REVIEW_REQUIRED',
                motion_writes=0, configuration_writes=0, servo_port_opened=False,
                elapsed_s=ended-began, mount_verified_in_config=cfg.get('imu_mount_verified') is True,
                angle_0x53=packet_stats(records, 0x53, began, ended),
                gyro_0x52=packet_stats(records, 0x52, began, ended),
                bad_checksum=status['bad_checksum'], samples=samples,
                sign_convention='body x forward, y left, z up; pitch_delta positive = front tilt, negative = rear tilt',
                note='Host receipt statistics are not sensor latency measurements; human direction confirmation is still required.')
