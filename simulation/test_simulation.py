"""Headless model checks; no hardware or display needed."""
import contextlib
import io
from types import SimpleNamespace
import unittest

import numpy as np
import run


class SimulationTest(unittest.TestCase):
    def test_reference_assets_and_actor_contract(self):
        manifest = run.verify_assets()
        m = run.build_model()
        self.assertEqual(m.nu, 14)
        self.assertEqual(m.njnt, 16)  # 15 hinges + floating root
        self.assertAlmostEqual(float(m.body_mass.sum()), .611, places=8)
        self.assertEqual([m.actuator(i).name for i in range(m.nu)], manifest["actor_names"])

    def test_suspended_model_removes_only_root_degree_of_freedom(self):
        free, fixed = run.build_model(), run.build_model(suspended=True)
        self.assertEqual(free.nq-fixed.nq, 7)
        self.assertEqual(free.nv-fixed.nv, 6)
        self.assertAlmostEqual(float(free.body_mass.sum()), float(fixed.body_mass.sum()))

    def test_payload_mass_is_additive(self):
        m = run.build_model(payload=run.HERE/"payload_example.json")
        self.assertAlmostEqual(float(m.body_mass.sum()), .695, places=8)
        self.assertEqual(m.nu, 14)

    def test_bounded_joint_probe_integrates_without_warning(self):
        args = SimpleNamespace(mode="joint", seconds=2., payload=None, image=None, video=None,
                               viewer=False, output=None, ffmpeg=None)
        with contextlib.redirect_stdout(io.StringIO()):
            r = run.run(args)
        self.assertEqual(r["steps"], 400)
        self.assertEqual(sum(r["warning_counts"]), 0)
        self.assertTrue(r["complete"])
        self.assertFalse(r["hardware_io"])
        self.assertGreater(r["joint_motion_range_deg"]["left_knee"], 3)
        self.assertGreater(r["joint_motion_range_deg"]["right_knee"], 3)
        self.assertEqual(r["target_clip_rad"], 0.)


if __name__ == "__main__":
    unittest.main()
