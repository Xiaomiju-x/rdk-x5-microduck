"""Hardware-free regression: packet guard, real runner, cancellation and setup."""
import contextlib
import copy
import hashlib
import io
import json
import sys
import tempfile
import threading
import time
import unittest
import urllib.request
import urllib.error
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
# The fake module makes tests runnable before pyserial installation too.
fake_serial=SimpleNamespace(SerialTimeoutException=type('SerialTimeoutException',(Exception,),{}),Serial=None)
try:import serial
except ImportError:sys.modules['serial']=fake_serial
import runtime
from app import Manager,make_handler,ThreadingHTTPServer
from contract import IDS,ALL_IDS,PositionGuard,position_packet
from neck import NeckPrefixCompensation
from parameters import validate_cycles

def cfg():
    value=runtime.read_json(runtime.HERE/'config/robot.example.json')
    value.update(runtime.reference());value.pop('purpose',None);value.pop('mount_status',None)
    value.update(servo_port='FAKE_SERVO',imu_port='FAKE_IMU',directions_verified=True,start_pose_verified=True,imu_mount_verified=True)
    return value

class Clock:
    def __init__(self):self.t=1.
    def monotonic(self):return self.t
    def sleep(self,v):self.t=round(self.t+max(0.,v),12)

class Sim:
    def __init__(self,configuration,clock):
        self.cfg=configuration;self.clock=clock;self.targets=runtime.integer_map(configuration['start'],'start')
        self.positions=dict(self.targets);self.torque={i:1 for i in ALL_IDS};self.packets=[];self.writes=[]
        self.imu_starts=0;self.imu_stops=0;self.opens=0;self.fault_after=None;self.stale_after=None;self.read_delay=0.
    def open(self,configuration,guard=None):
        self.opens+=1;sim=self
        class Wire:
            timeout=.005
            def write(self,p):
                sim.packets.append(bytes(p))
                if p[4]==0x83:
                    for k in range(7,len(p)-1,3):sim.targets[p[k]]=p[k+1]+256*p[k+2];sim.positions[p[k]]=sim.targets[p[k]]
                return len(p)
            def flush(self):pass
            def close(self):pass
        wire=Wire()
        class Bus:
            def __init__(self):self.ser=guard(wire) if guard else wire;self.stats={'rx_ok':0,'timeout':0,'bad_checksum':0,'bad_id':0}
            def read(self,sid,origin,length):
                data=bytearray(66);data[5]=sid;data[33]=4;data[40]=sim.torque[sid];data[62]=50;data[63]=30
                data[31:33]=sim.cfg['expected_offsets_raw'][str(sid)].to_bytes(2,'little')
                data[42:44]=sim.targets[sid].to_bytes(2,'little');data[56:58]=sim.positions[sid].to_bytes(2,'little')
                if sim.fault_after is not None and len(sim.packets)>=sim.fault_after and sid==4:data[40]=0
                self.stats['rx_ok']+=1;return 0,bytes(data[origin:origin+length])
            def sync_read(self,ids,origin,length):
                sim.clock.sleep(sim.read_delay)
                return {i:self.read(i,origin,length) for i in ids}
            def sync_write(self,address,width,rows):
                args=bytes([address,width])+b''.join(bytes([i])+v for i,v in rows)
                body=bytes([254,len(args)+2,0x83])+args
                self.ser.write(b'\xff\xff'+body+bytes([255-sum(body)%256]))
            def write(self,sid,address,data):
                sim.writes.append((sid,address,list(data)))
                if address==42:sim.targets[sid]=int.from_bytes(data,'little');sim.positions[sid]=sim.targets[sid]
                elif address==40:sim.torque[sid]=data[0]
                else:raise AssertionError('Unexpected configuration write')
            def close(self):self.ser.close()
        return Bus()
    def imu(self,*_):
        sim=self
        class Imu:
            def start(self):sim.imu_starts+=1
            def snapshot(self):
                return {'sensor_angles_deg':[0,0,0],'host_age_ms':151 if sim.stale_after is not None and len(sim.packets)>=sim.stale_after else 0,'error':None}
            def stop(self):sim.imu_stops+=1;return {'stopped':True}
        return Imu()

class RuntimeTests(unittest.TestCase):
    def exercise(self,cycles,stop_at=None,fault_at=None,stale_at=None,read_delay=0):
        configuration=cfg();clock=Clock();sim=Sim(configuration,clock)
        sim.fault_after=fault_at;sim.stale_after=stale_at;sim.read_delay=read_delay
        def cancel():
            if stop_at is not None and len(sim.packets)>=stop_at:raise RuntimeError('Operator stop')
        outcome=None;failure=None
        with tempfile.TemporaryDirectory() as tmp,contextlib.ExitStack() as stack:
            stack.enter_context(patch.object(runtime,'open_bus',sim.open));stack.enter_context(patch.object(runtime,'ImuTrace',sim.imu))
            stack.enter_context(patch.object(runtime.time,'monotonic',clock.monotonic));stack.enter_context(patch.object(runtime.time,'sleep',clock.sleep))
            try:outcome=runtime.run(configuration,runtime.defaults(),cycles,cancel=cancel,record_dir=Path(tmp)/'records')
            except Exception as exc:failure=exc
            receipts=[runtime.read_json(p) for p in (Path(tmp)/'records').glob('*.json')]
        return sim,outcome,failure,receipts,clock.t
    def test_defaults(self):
        p=runtime.defaults();self.assertEqual((p['bias_deg'],p['motion_deg'],p['return_advance_s'],p['transition_s']),(0,-30,1.1,.2))
        self.assertEqual(p['gain'],0);self.assertEqual(p['back_gain'],0)
    def test_plan_never_opens_serial(self):
        with patch.object(runtime,'open_bus',side_effect=AssertionError('hardware')):
            self.assertEqual(runtime.plan(cycles=5)['total_frames'],2000)
    def test_cycles_strict(self):
        for bad in (True,0,4,6,1.0,'2'):
            with self.assertRaises(ValueError):validate_cycles(bad)
    def test_template_cannot_move(self):
        with self.assertRaises(ValueError):runtime.validate_device(runtime.read_json(runtime.HERE/'config/robot.example.json'),motion=True,imu=True)
    def test_reference_is_not_device_config(self):
        with self.assertRaises(ValueError):runtime.validate_device(runtime.reference(),motion=True,imu=True)
    def test_serial_rotation_and_verified_flags(self):
        for key in ('directions_verified','start_pose_verified','imu_mount_verified'):
            c=cfg();c[key]=False
            with self.assertRaises(ValueError):runtime.validate_device(c,motion=True,imu=True)
        c=cfg();c['body_from_sensor_rotation']=[[0]*3 for _ in range(3)]
        with self.assertRaises(ValueError):runtime.validate_device(c,motion=True,imu=True)
    def test_plan_delta_translation(self):
        s=runtime.integer_map(cfg()['start'],'start');other={i:v+10 for i,v in s.items()}
        a=runtime.build_frames(s);b=runtime.build_frames(other)
        for x,y in zip(a,b):
            self.assertEqual(x['interval_s'],y['interval_s']);self.assertTrue(all(y['target'][i]-x['target'][i]==10 for i in ALL_IDS))
    def test_neck_finishes_and_legs_unchanged(self):
        start=runtime.integer_map(cfg()['start'],'start');frames=runtime.build_frames(start)
        for motion in (-30,0,8):
            p=runtime.defaults();p['motion_deg']=motion;neck=NeckPrefixCompensation(parameters=p);prev=dict(start)
            for k,f in enumerate(frames):
                target,_=neck.apply(k,0,f['target'],start,prev,motion_elapsed_s=max(0,(k-150)*.02))
                self.assertTrue(all(target[i]==f['target'][i] for i in ALL_IDS if i!=11));prev=target
            self.assertEqual(prev,start)
    def test_packet_guard_forbids_torque_and_configuration(self):
        class Wire:
            def write(self,p):return len(p)
        start=runtime.integer_map(cfg()['start'],'start');guard=PositionGuard(Wire(),start,runtime.defaults())
        for address in (5,21,22,31,40,55):
            body=bytes([1,4,3,address,1]);packet=b'\xff\xff'+body+bytes([255-sum(body)%256])
            with self.assertRaises(ValueError):guard.write(packet)
        guard.allowed=dict(start);self.assertEqual(guard.write(position_packet(start)),50)
    def test_complete_1_2_3_5_byte_identical(self):
        baseline=None
        for n in (1,2,3,5):
            sim,out,err,logs,elapsed=self.exercise(n)
            self.assertIsNone(err,str(err));self.assertEqual(out['cycles_completed'],n);self.assertEqual(len(sim.packets),400*n)
            if baseline is None:baseline=sim.packets
            for k in range(n):self.assertEqual(sim.packets[k*400:(k+1)*400],baseline)
            evidence=runtime.read_json(runtime.HERE/'data/offline_equivalence.json')
            expected=next(x for x in evidence['cases'] if x['cycles']==n)
            self.assertEqual(hashlib.sha256(b''.join(sim.packets)).hexdigest(),expected['packets_sha256'])
            self.assertEqual(sim.imu_starts,n);self.assertEqual(sim.imu_stops,n);self.assertFalse(sim.writes)
            if n==5:self.assertGreater(elapsed,20)
            self.assertEqual(logs[0]['status'],'COMPLETE_ONSITE_RESULT_PENDING')
    def test_stop_between_cycles(self):
        sim,out,err,logs,_=self.exercise(5,stop_at=400)
        self.assertIsNotNone(err);self.assertEqual(len(sim.packets),400);self.assertEqual(sim.opens,1);self.assertEqual(logs[0]['cycles_completed'],1)
    def test_stop_during_second_cycle(self):
        sim,_,err,logs,_=self.exercise(5,stop_at=411)
        self.assertIsNotNone(err);self.assertEqual(len(sim.packets),411);self.assertEqual(sim.opens,2);self.assertEqual(logs[0]['cycles_completed'],1)
    def test_fault_during_second_cycle(self):
        sim,_,err,logs,_=self.exercise(5,fault_at=411)
        self.assertIsNotNone(err);self.assertEqual(len(sim.packets),411);self.assertEqual(sim.opens,2);self.assertFalse(sim.writes)
    def test_stale_imu_stops_batch(self):
        sim,_,err,logs,_=self.exercise(5,stale_at=100)
        self.assertIsNotNone(err);self.assertEqual(len(sim.packets),100);self.assertEqual(logs[0]['cycles_completed'],0)
    def test_slow_reads_no_catchup(self):
        sim,_,err,logs,_=self.exercise(2,read_delay=.025)
        self.assertIsNone(err);self.assertEqual(len(sim.packets),800)
        self.assertGreater(logs[0]['cycles'][0]['elapsed_s'],9)
    def test_identity_offset_mode_refused(self):
        sim=Sim(cfg(),Clock());bus=sim.open(cfg());err,data=bus.read(1,0,66)
        for index in (5,31,33):
            changed=bytearray(data);changed[index]+=1
            with self.assertRaises(RuntimeError):runtime.check_identity(1,err,changed,cfg())
    def test_capture_readonly_and_requires_review(self):
        configuration=cfg();clock=Clock();sim=Sim(configuration,clock)
        with tempfile.TemporaryDirectory() as tmp,patch.object(runtime,'open_bus',sim.open),patch.object(runtime.time,'sleep',clock.sleep):
            output=Path(tmp)/'robot.json';result=runtime.capture_start(configuration,output,Path(tmp)/'records')
            saved=runtime.read_json(output);self.assertFalse(saved['start_pose_verified']);self.assertEqual(result['motion_writes'],0)
        self.assertFalse(sim.packets);self.assertFalse(sim.writes)
    def test_restore_capture_before_enable_and_no_pd(self):
        configuration=cfg();clock=Clock();sim=Sim(configuration,clock)
        for i in ALL_IDS:sim.torque[i]=0;sim.positions[i]+=20
        with tempfile.TemporaryDirectory() as tmp,patch.object(runtime,'open_bus',sim.open),patch.object(runtime.time,'sleep',clock.sleep):
            out=runtime.restore(configuration,record_dir=Path(tmp)/'records')
        self.assertEqual(out['status'],'COMPLETE_SUPPORTED_RESTORE')
        for sid in ALL_IDS:
            writes=[w for w in sim.writes if w[0]==sid]
            self.assertEqual([w[1] for w in writes],[42,40]);self.assertEqual(writes[1][2],[1]);self.assertEqual(sim.targets[sid],configuration['start'][str(sid)])
    def test_partial_restore_skips_large_axis(self):
        configuration=cfg();clock=Clock();sim=Sim(configuration,clock);sim.positions[4]-=600
        with tempfile.TemporaryDirectory() as tmp,patch.object(runtime,'open_bus',sim.open),patch.object(runtime.time,'sleep',clock.sleep):
            out=runtime.restore(configuration,record_dir=Path(tmp)/'records',partial=True)
        self.assertIn('4',out['skipped']);self.assertFalse(any(w[0]==4 for w in sim.writes))
    def test_full_restore_bad_axis_writes_nothing(self):
        configuration=cfg();clock=Clock();sim=Sim(configuration,clock);sim.positions[4]-=600
        with tempfile.TemporaryDirectory() as tmp,patch.object(runtime,'open_bus',sim.open):
            with self.assertRaises(ValueError):runtime.restore(configuration,record_dir=Path(tmp)/'records')
        self.assertFalse(sim.writes);self.assertFalse(sim.packets)

class PanelTests(unittest.TestCase):
    def test_no_action_on_init_and_saved_preset_independent_of_cycles(self):
        with tempfile.TemporaryDirectory() as tmp,patch.object(runtime,'open_bus',side_effect=AssertionError('hardware')):
            m=Manager(data_dir=tmp);self.assertFalse(m.status()['busy']);self.assertIsNone(m.status()['current'])
            p=runtime.defaults();p['bias_deg']=.5;m.save(p)
            self.assertNotIn('cycles',runtime.read_json(Path(tmp)/'preset.json'))
    def test_ready_flags_required(self):
        with tempfile.TemporaryDirectory() as tmp:
            m=Manager(data_dir=tmp)
            for action in ('run','restore','partial_restore'):
                with self.assertRaises(ValueError):m.start({'action':action})
    def test_demo_2_cycles_and_mutex(self):
        with tempfile.TemporaryDirectory() as tmp:
            m=Manager(data_dir=tmp,demo_scale=.001)
            entered=threading.Event();release=threading.Event();finished=threading.Event()
            real_work=m._work
            def controlled_sleep(_seconds):
                # Gate the first worker sleep so the mutex assertion cannot race completion.
                # Later DEMO delays are skipped only in this test; app timing stays unchanged.
                if not entered.is_set():
                    entered.set()
                    if not release.wait(10):raise RuntimeError('Test did not release the DEMO worker')
            def observed_work(*args):
                try:return real_work(*args)
                finally:finished.set()
            m._work=observed_work
            # Replace app's reference, not the shared time module (or the test's own waits).
            with patch('app.time',SimpleNamespace(time=time.time,sleep=controlled_sleep)):
                m.start({'action':'run','onsite_ready':True,'cycles':2})
                try:
                    self.assertTrue(entered.wait(10),'DEMO worker did not enter')
                    with self.assertRaises(ValueError):m.start({'action':'run','onsite_ready':True})
                finally:release.set()
                self.assertTrue(finished.wait(10),'DEMO worker did not finish')
            self.assertEqual(m.current['status'],'completed');self.assertEqual(m.current['result']['cycles_completed'],2)
            self.assertEqual(m.current['result']['motion_writes'],0)
            self.assertEqual(m.current['progress']['global_frame'],800)
            self.assertFalse(m.status()['busy'])
    def test_http_same_origin_and_token(self):
        with tempfile.TemporaryDirectory() as tmp:
            m=Manager(data_dir=tmp);server=ThreadingHTTPServer(('127.0.0.1',0),make_handler(m));thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
            base=f'http://127.0.0.1:{server.server_port}'
            try:
                c=json.load(urllib.request.urlopen(base+'/api/config'));self.assertTrue(c['demo'])
                req=urllib.request.Request(base+'/api/stop',data=b'{}',headers={'Content-Type':'application/json'},method='POST')
                with self.assertRaises(urllib.error.HTTPError):urllib.request.urlopen(req)
                req.add_header('X-Control-Token',c['token']);self.assertTrue(json.load(urllib.request.urlopen(req))['stop_requested'])
                req.add_header('Origin','http://untrusted.invalid')
                with self.assertRaises(urllib.error.HTTPError):urllib.request.urlopen(req)
            finally:server.shutdown();server.server_close();thread.join()

if __name__=='__main__':unittest.main()
