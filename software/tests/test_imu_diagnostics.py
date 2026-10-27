"""Offline IMU diagnostic checks. No serial device is opened."""
import copy
import math
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import runtime
from imu_diagnostics import body_values, inspect_imu, validate_imu_config


class Clock:
    def __init__(self): self.t = 1.
    def monotonic(self): return self.t
    def sleep(self, dt): self.t = round(self.t+dt, 10)


class FakeTrace:
    def __init__(self, clock, stale=False, fail_start=False):
        self.clock=clock; self.stale=stale; self.fail_start=fail_start
        self.records=[]; self.latest={}; self.next_stamp=1.; self.stopped=False
    def start(self):
        if self.fail_start: raise RuntimeError('No valid IMU baseline')
    def snapshot(self):
        now=self.clock.monotonic()
        while self.next_stamp <= now+1e-9:
            pitch=(self.next_stamp-1)*2
            a=dict(kind=0x53, mono_s=self.next_stamp, sensor_angles_deg=[0,pitch,0])
            g=dict(kind=0x52, mono_s=self.next_stamp, sensor_gyro_dps=[0,2,0])
            self.records.extend([a,g]); self.latest.update({0x53:a,0x52:g})
            self.next_stamp=round(self.next_stamp+.02,10)
        return dict(sensor_angles_deg=self.latest[0x53]['sensor_angles_deg'],
                    host_age_ms=151 if self.stale else (now-self.latest[0x53]['mono_s'])*1000,error=None)
    def stop(self):
        self.stopped=True
        return dict(records=self.records,bad_checksum=0,error=None,thread_stopped=True)


class ImuDiagnosticTests(unittest.TestCase):
    def config(self):
        return dict(imu_port='FAKE_IMU',imu_baud=115200,imu_mount_verified=False,
                    body_from_sensor_rotation=np.eye(3).tolist())
    def test_default_frame_sign_matches_runtime(self):
        for angles in ([0,10,0],[0,-10,20],[5,20,0]):
            r=np.eye(3); v=body_values(angles,[1,2,3],r)
            self.assertAlmostEqual(v['body_pitch_deg'],runtime.candidate_pitch({'sensor_angles_deg':angles},r),places=8)
        self.assertGreater(body_values([0,10,0],[0,0,0],np.eye(3))['body_pitch_deg'],0)
    def test_rotation_columns_map_sensor_to_body(self):
        r=np.array([[0,-1,0],[1,0,0],[0,0,1]])
        self.assertEqual(body_values([0,0,0],[1,0,0],r)['body_gyro_dps'],[0.,1.,0.])
    def test_invalid_rotation_refused_before_trace(self):
        for matrix in ([[0]*3]*3,[[1,0,0],[0,1,0],[0,0,-1]],[[math.nan,0,0],[0,1,0],[0,0,1]]):
            cfg=self.config(); cfg['body_from_sensor_rotation']=matrix
            with patch('imu_diagnostics.ImuTrace',side_effect=AssertionError('opened')):
                with self.assertRaises(ValueError): validate_imu_config(cfg)
    def test_missing_port_refused(self):
        cfg=self.config();cfg['imu_port']='SET_IMU_PORT'
        with self.assertRaises(ValueError): validate_imu_config(cfg)
    def test_wrong_baud_refused(self):
        cfg=self.config();cfg['imu_baud']=9600
        with self.assertRaises(ValueError): validate_imu_config(cfg)
    def test_bad_durations_before_any_reader(self):
        for seconds in (0,61,float('inf'),float('nan'),True,'5'):
            with self.assertRaises(ValueError): inspect_imu(self.config(),seconds,trace_factory=lambda *_:self.fail('opened'))
    def test_inspection_does_not_need_servo_or_verified_flags(self):
        cfg=self.config();before=copy.deepcopy(cfg);clock=Clock();trace=FakeTrace(clock)
        with patch.object(runtime,'open_bus',side_effect=AssertionError('servo touched')):
            result=inspect_imu(cfg,5,trace_factory=lambda *_:trace,clock=clock)
        self.assertEqual(cfg,before);self.assertTrue(trace.stopped)
        self.assertFalse(result['servo_port_opened']);self.assertEqual(result['motion_writes'],0)
        self.assertEqual(result['configuration_writes'],0);self.assertFalse(result['mount_verified_in_config'])
        self.assertGreater(result['angle_0x53']['host_observed_hz'],45)
        self.assertGreater(result['samples'][-1]['pitch_delta_deg'],9)
    def test_stale_stream_closes_reader(self):
        clock=Clock();trace=FakeTrace(clock,stale=True)
        with self.assertRaisesRegex(RuntimeError,'stale'):
            inspect_imu(self.config(),1,trace_factory=lambda *_:trace,clock=clock)
        self.assertTrue(trace.stopped)
    def test_start_failure_closes_reader(self):
        trace=FakeTrace(Clock(),fail_start=True)
        with self.assertRaises(RuntimeError):inspect_imu(self.config(),1,trace_factory=lambda *_:trace)
        self.assertTrue(trace.stopped)
    def test_cancel_closes_reader(self):
        trace=FakeTrace(Clock())
        def cancel():raise RuntimeError('Operator stop')
        with self.assertRaisesRegex(RuntimeError,'Operator stop'):
            inspect_imu(self.config(),1,cancel=cancel,trace_factory=lambda *_:trace)
        self.assertTrue(trace.stopped)


if __name__=='__main__':unittest.main()
