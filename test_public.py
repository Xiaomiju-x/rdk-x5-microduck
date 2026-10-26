import json
import unittest
from pathlib import Path
from duck_tuning_config_20260929 import DEFAULTS,validate_parameters
from neck_prefix_compensation_20260929 import NeckPrefixCompensation
from imu_trace_20260927 import Parser

class PublicOfflineTests(unittest.TestCase):
    def test_parameter_range(self):
        self.assertEqual(validate_parameters(dict(gain=.375,max_back_deg=4.,deadband_deg=1.))['gain'],.375)
        with self.assertRaises(ValueError):validate_parameters({**DEFAULTS,'gain':float('nan')})
    def test_no_compensation_for_constant_pitch(self):
        ctrl=NeckPrefixCompensation(parameters=dict(gain=.375,max_back_deg=4.,deadband_deg=1.))
        r3={i:2048 for i in range(1,16)};previous=r3.copy()
        for k in range(400):
            goal,_=ctrl.apply(k,0.,r3,r3,previous)
            self.assertEqual(goal,r3);previous=goal
    def test_compensation_returns_to_r3(self):
        ctrl=NeckPrefixCompensation(parameters=dict(gain=.375,max_back_deg=4.,deadband_deg=1.))
        r3={i:2048 for i in range(1,16)};previous=r3.copy()
        for k in range(400):
            goal,_=ctrl.apply(k,12. if 150<=k<250 else 0.,r3,r3,previous)
            self.assertTrue(0<=goal[11]-2048<=46)
            self.assertTrue(all(goal[i]==2048 for i in r3 if i!=11));previous=goal
        self.assertEqual(goal,r3)
    def test_imu_checksum(self):
        packet=bytearray([0x55,0x53,0,0,0,0,0,0,0,0]);packet.append(sum(packet)&255)
        self.assertEqual(Parser().feed(packet,0.)[0]['sensor_angles_deg'],[0.,0.,0.])
    def test_offline_fixture(self):
        p=Path(__file__).with_name('recorded_prefix_fixture.json')
        if not p.exists():self.skipTest('fixture provided in source ZIP')
        d=json.loads(p.read_text(encoding='utf8'))
        self.assertEqual(len(d['frames']),250)
        self.assertTrue(all(f['sent_targets']==d['r3'] for f in d['frames'][:150]))

if __name__=='__main__':unittest.main()
