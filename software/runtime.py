"""Portable D controller. Import/plan never opens a serial device.

Same 400-frame deltas, timing and neck algorithm as the successful prototype.
Hardware I/O is explicit. This packaging is offline verified, not a new gait.
"""
import argparse
import contextlib
import hashlib
import json
import math
import signal
import threading
import time
from pathlib import Path

import numpy as np
from contract import ALL_IDS, IDS, PositionGuard, check_target
from parameters import validate_parameters, validate_cycles
from neck import NeckPrefixCompensation
from feedback import decode_and_check
from bounded_read import BoundedHeadRead
from confirm_write import confirm_position_write
from imu import ImuTrace

HERE=Path(__file__).resolve().parent

def read_json(path):return json.loads(Path(path).read_text(encoding='utf8'))
def write_json(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix(path.suffix+'.tmp')
    temp.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    temp.replace(path)
def defaults():return validate_parameters(read_json(HERE/'config/success_20261023.json'))
def reference():return read_json(HERE/'data/reference_pose_NOT_A_DEVICE_CONFIG.json')

def integer_map(value,label,upper=4095):
    if not isinstance(value,dict) or set(value)!=set(map(str,ALL_IDS)):
        raise ValueError(label+' must contain string IDs 1..15')
    if any(type(v) is not int or not 0<=v<=upper for v in value.values()):
        raise ValueError(label+' contains missing/out-of-range values')
    return {int(k):v for k,v in value.items()}

def validate_device(cfg,motion=False,imu=False):
    if cfg.get('schema')!=1 or cfg.get('model')!='FT_HD1910M_15' or cfg.get('expected_mode')!=4:
        raise ValueError('Only the documented FT HD1910M 15-axis position-mode setup is supported')
    for name in ('servo_port',)+(('imu_port',) if imu else ()):
        if not isinstance(cfg.get(name),str) or not cfg[name] or cfg[name].startswith('SET_'):
            raise ValueError('Set '+name+' in your local robot configuration')
    if cfg.get('servo_baud')!=1000000 or cfg.get('imu_baud')!=115200:
        raise ValueError('This reference expects servo 1M and JY901S 115200 baud; it never changes baud rates')
    if motion:
        start=integer_map(cfg.get('start'),'start')
        integer_map(cfg.get('expected_offsets_raw'),'expected_offsets_raw',65535)
        if cfg.get('directions_verified') is not True or cfg.get('start_pose_verified') is not True:
            raise ValueError('Verify the actual ID/direction and START pose before motion')
        build_frames(start)  # All 400 goals must fit this device before I/O.
    if imu:
        if cfg.get('imu_mount_verified') is not True:raise ValueError('Verify the fixed IMU mounting')
        rotation=np.asarray(cfg.get('body_from_sensor_rotation'),dtype=float)
        if rotation.shape!=(3,3) or not np.isfinite(rotation).all() or not np.allclose(rotation.T@rotation,np.eye(3),atol=1e-6) or not np.isclose(np.linalg.det(rotation),1,atol=1e-6):
            raise ValueError('body_from_sensor_rotation must be a finite proper 3x3 rotation')
    return cfg

def build_frames(start):
    raw=(HERE/'data/d_trajectory.json').read_bytes()
    if hashlib.sha256(raw).hexdigest()!=read_json(HERE/'data/provenance.json')['trajectory_sha256']:
        raise ValueError('Published trajectory checksum mismatch')
    rows=json.loads(raw)['frames'];previous=dict(start);frames=[]
    if len(rows)!=400:raise ValueError('D must contain exactly 400 frames')
    for k,row in enumerate(rows):
        if len(row['delta'])!=15 or any(type(d) is not int for d in row['delta']):raise ValueError('Invalid delta')
        if type(row['interval_s']) not in (int,float) or not .018<=row['interval_s']<=.05:raise ValueError('Invalid interval')
        target={i:start[i]+row['delta'][i-1] for i in ALL_IDS}
        check_target(target,start,previous)
        if k<150 and target!=start:raise ValueError('Preparation must hold START')
        frames.append({'target':target,'interval_s':row['interval_s'],'phase':row['phase']});previous=target
    if frames[-1]['target']!=start:raise ValueError('Missing START endpoint')
    return frames

def plan(cfg=None,parameters=None,cycles=1):
    parameters=validate_parameters(parameters or defaults());validate_cycles(cycles)
    start=integer_map((cfg or reference())['start'],'start')
    frames=build_frames(start);neck=NeckPrefixCompensation(parameters=parameters);previous=dict(start);issued=[]
    for k,f in enumerate(frames):
        target,detail=neck.apply(k,0.,f['target'],start,previous,motion_elapsed_s=max(0.,sum(x['interval_s'] for x in frames[151:k+1])))
        extra=8. if parameters['neck_mode']=='legacy_offset' and (parameters['bias_deg'] or parameters['back_gain']) else 0.
        check_target(target,start,previous,extra,20. if parameters['neck_mode']=='two_stage_pose' else 0.)
        previous=target;issued.append(target)
    return dict(execute=False,motion_writes=0,cycles=cycles,frames_per_cycle=400,total_frames=400*cycles,
                nominal_seconds_per_cycle=sum(f['interval_s'] for f in frames),parameters=parameters,
                all_cycle_endpoints_start=issued[-1]==start,
                target_sha256=hashlib.sha256(json.dumps([[t[i] for i in ALL_IDS] for t in issued],separators=(',',':')).encode()).hexdigest())

def decode(data):
    if len(data)!=66:raise ValueError('Incomplete full status')
    w=lambda a:data[a]+256*data[a+1]
    raw=w(56)
    return dict(id=data[5],mode=data[33],offset=w(31),torque=data[40],target=w(42),
                pos=-(raw&32767) if raw&32768 else raw,voltage=data[62]/10,temp=data[63],error=data[65])

def check_identity(sid,error,data,cfg):
    q=decode(data)
    if q['id']!=sid or q['mode']!=cfg['expected_mode']:raise RuntimeError('ID/mode mismatch '+str(sid))
    offset=cfg['expected_offsets_raw'].get(str(sid))
    if offset is not None and q['offset']!=offset:raise RuntimeError('Hardware offset changed '+str(sid))
    if (error|q['error'])&~1 or not 0<=q['pos']<=4095 or not 0<q['voltage']<=8.4:
        raise RuntimeError('Servo fault or invalid coordinate '+str((sid,q)))
    return q

def read_all(bus,cfg,expected=None):
    result={}
    for sid in ALL_IDS:
        err,data=bus.read(sid,0,66);q=check_identity(sid,err,data,cfg)
        if expected is not None:decode_and_check(sid,err,data,0,expected)
        result[sid]=q
    return result

@contextlib.contextmanager
def ownership(port,folder):
    """One process owns the entire batch, including between cycles."""
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    path=folder/('serial_'+hashlib.sha256(port.encode()).hexdigest()[:16]+'.lock')
    with path.open('a+b') as f:
        f.seek(0);f.write(b'0');f.flush();f.seek(0)
        try:
            if __import__('os').name=='nt':
                import msvcrt;msvcrt.locking(f.fileno(),msvcrt.LK_NBLCK,1)
            else:
                import fcntl;fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except OSError as exc:raise RuntimeError('Another controller owns this serial device') from exc
        try:yield
        finally:
            f.seek(0)
            if __import__('os').name=='nt':msvcrt.locking(f.fileno(),msvcrt.LK_UNLCK,1)
            else:fcntl.flock(f,fcntl.LOCK_UN)

def open_bus(cfg,guard=None):
    import serial
    from vendor.feetech import FeetechBus
    raw=serial.Serial(cfg['servo_port'],cfg['servo_baud'],timeout=.005,write_timeout=.05,exclusive=True)
    try:return FeetechBus(cfg['servo_port'],ser=guard(raw) if guard else raw)
    except BaseException:raw.close();raise

def candidate_pitch(snapshot,rotation):
    # Same float32 sensor gravity and fixed rotation as the original runtime.
    r,p,_=np.radians(np.asarray(snapshot['sensor_angles_deg'],dtype=np.float32)).astype(float)
    gravity=np.array([math.sin(p),-math.sin(r)*math.cos(p),-math.cos(r)*math.cos(p)],dtype=np.float32)
    body=rotation@gravity
    return float(np.degrees(np.arctan2(body[0],np.hypot(body[1],body[2]))))

def run_cycle(cfg,parameters,bus,imu,progress,cancel,clock=time,events=None):
    """One cycle. Fresh neck reference/deadline/retry budget on every call."""
    from vendor.feetech import BusTimeout
    import serial
    events=[] if events is None else events
    start=integer_map(cfg['start'],'start');frames=build_frames(start)
    neck=NeckPrefixCompensation(parameters=parameters)
    reader=BoundedHeadRead(bus,BusTimeout,serial.SerialTimeoutException)
    ambiguous=[];expected=dict(start);rotation=np.asarray(cfg['body_from_sensor_rotation'])
    read_all(bus,cfg,expected);imu.start();epoch=clock.monotonic();last=None;neck_epoch=None
    for k,frame in enumerate(frames):
        cancel();begun=clock.monotonic()
        rows=bus.sync_read(list(range(1,11)),40,26)
        for sid in range(11,16):rows[sid]=reader.read(sid,k)
        if set(rows)!=set(start) or any(v is None for v in rows.values()):raise RuntimeError('Incomplete actuator feedback')
        states={sid:decode_and_check(sid,*rows[sid],40,expected) for sid in rows}
        if last is not None:clock.sleep(max(0,last+frame['interval_s']-clock.monotonic()))
        if clock.monotonic()-epoch>20:raise RuntimeError('Finite per-cycle deadline')
        cancel();snapshot=imu.snapshot()
        if not snapshot or snapshot['error'] or snapshot['host_age_ms']>150:raise RuntimeError('Fresh IMU required')
        pitch=candidate_pitch(snapshot,rotation)
        if k>=150 and neck_epoch is None:neck_epoch=clock.monotonic()
        elapsed=None if neck_epoch is None else clock.monotonic()-neck_epoch
        target,neck_log=neck.apply(k,pitch,frame['target'],start,expected,motion_elapsed_s=elapsed)
        bus.ser.allowed=target
        try:
            bus.sync_write(42,2,[(sid,target[sid].to_bytes(2,'little')) for sid in sorted(IDS)])
            bus.ser.raw.flush()
        except serial.SerialTimeoutException as exc:confirm_position_write(bus,target,k,ambiguous,exc)
        stamp=clock.monotonic()
        events.append(dict(frame=k,phase=frame['phase'],sent_targets=target,state_before_command=states,
                           t_s=stamp-epoch,source_interval_s=frame['interval_s'],imu=snapshot,neck=neck_log))
        expected=target;last=stamp
        if k%10==0 or k==399:progress(dict(frame=k+1,total=400,phase=frame['phase'],pitch_deg=pitch,
             neck_requested_deg=neck_log.get('requested_total_deg'),neck_actual=states[11]['pos'],minimum_voltage=min(q['voltage'] for q in states.values())))
    after=read_all(bus,cfg,start)
    if len(events)!=400 or expected!=start:raise RuntimeError('Incomplete cycle')
    return dict(status='COMPLETE_START_HELD_ONSITE_RESULT_PENDING',frames=400,after=after,
                head_read_retries=reader.events,ambiguous_write_events=ambiguous,elapsed_s=clock.monotonic()-epoch)

def run(cfg,parameters,cycles,progress=lambda _:None,cancel=lambda:None,record_dir=HERE/'.local/records'):
    validate_device(cfg,motion=True,imu=True);parameters=validate_parameters(parameters);validate_cycles(cycles)
    plan(cfg,parameters,cycles)  # Range checks before opening devices.
    result={'action':'run','cycles_requested':cycles,'cycles_completed':0,'parameters':parameters,'cycles':[],
            'status':'RUNNING','configuration_writes':0,'torque_writes':0}
    path=Path(record_dir)/('run_'+str(time.time_ns())+'.json')
    try:
        with ownership(cfg['servo_port'],Path(record_dir).parent/'locks'):
            for cycle in range(1,cycles+1):
                cancel();start=integer_map(cfg['start'],'start')
                bus=open_bus(cfg,lambda raw:PositionGuard(raw,start,parameters));imu=ImuTrace(cfg['imu_port'],cfg['imu_baud'])
                entry={'cycle':cycle,'events':[]};result['cycles'].append(entry)
                def report(row):progress({**row,'cycle':cycle,'cycles':cycles,'global_frame':(cycle-1)*400+row['frame'],'global_total':cycles*400})
                try:
                    entry.update(run_cycle(cfg,parameters,bus,imu,report,cancel,events=entry['events']))
                    result['cycles_completed']+=1
                finally:
                    entry['imu_trace']=imu.stop();entry['bus_stats']=dict(bus.stats);bus.close()
                cancel()
        result['status']='COMPLETE_ONSITE_RESULT_PENDING'
    except BaseException as exc:
        result.update(status='STOPPED_LAST_GOAL_HELD_NO_AUTO_RESTORE',failure=str(exc));raise
    finally:write_json(path,result)
    return {k:v for k,v in result.items() if k!='cycles'}|{'record':str(path)}

def inspect_device(cfg,record_dir=HERE/'.local/records'):
    validate_device(cfg)
    with ownership(cfg['servo_port'],Path(record_dir).parent/'locks'):
        bus=open_bus(cfg)
        try:return {'motion_writes':0,'state':read_all(bus,cfg)}
        finally:bus.close()

def capture_start(cfg,output,record_dir=HERE/'.local/records'):
    """Read actual positions only; never enable or command any joint."""
    validate_device(cfg)
    with ownership(cfg['servo_port'],Path(record_dir).parent/'locks'):
        bus=open_bus(cfg)
        try:
            rows=[]
            for _ in range(3):rows.append(read_all(bus,cfg));time.sleep(.1)
        finally:bus.close()
    for sid in ALL_IDS:
        if max(r[sid]['pos'] for r in rows)-min(r[sid]['pos'] for r in rows)>10:
            raise RuntimeError('Pose moved during capture: '+str(sid))
    updated=dict(cfg);updated['start']={str(i):rows[-1][i]['pos'] for i in ALL_IDS}
    updated['expected_offsets_raw']={str(i):rows[-1][i]['offset'] for i in ALL_IDS}
    updated['start_pose_verified']=False
    write_json(output,updated)
    return {'motion_writes':0,'output':str(output),'next':'Review the captured pose and directions; set start_pose_verified only after visual confirmation.'}

def restore(cfg,progress=lambda _:None,cancel=lambda:None,record_dir=HERE/'.local/records',partial=False):
    """Explicit supported reset: capture goals before enable; max six counts/tick."""
    validate_device(cfg,motion=True)
    start=integer_map(cfg['start'],'start');result={'action':'restore','events':[],'skipped':{},'configuration_writes':0}
    path=Path(record_dir)/('restore_'+str(time.time_ns())+'.json')
    try:
        with ownership(cfg['servo_port'],Path(record_dir).parent/'locks'):
            bus=open_bus(cfg)
            try:
                selected={};current={}
                for sid in ALL_IDS:
                    cancel()
                    try:
                        error,data=bus.read(sid,0,66);q=check_identity(sid,error,data,cfg)
                        if abs(q['pos']-start[sid])>512:raise ValueError('More than 45 degrees from START; reposition this axis while supported')
                        if q['torque'] not in (0,1):raise ValueError('Unexpected torque state')
                        selected[sid]=q;current[sid]=q['pos']
                    except Exception as exc:
                        if not partial:raise
                        result['skipped'][str(sid)]=str(exc)
                if not selected:raise RuntimeError('No restorable axes')
                # Each selected motor receives its measured current position BEFORE enable.
                for sid,q in selected.items():
                    cancel();goal=q['pos'];bus.write(sid,42,goal.to_bytes(2,'little'))
                    err,data=bus.read(sid,0,66);fresh=check_identity(sid,err,data,cfg)
                    if fresh['target']!=goal or abs(fresh['pos']-goal)>20:raise RuntimeError('Capture target not accepted '+str(sid))
                    if q['torque']==0:bus.write(sid,40,b'\x01')
                    err,data=bus.read(sid,0,66);fresh=check_identity(sid,err,data,cfg)
                    decode_and_check(sid,err,data,0,{sid:goal})
                count=max(1,math.ceil(max(abs(start[i]-current[i]) for i in current)/4))
                origin=dict(current)
                for k in range(1,count+1):
                    cancel();u=k/count;w=u*u*(3-2*u)
                    targets={i:round(origin[i]+(start[i]-origin[i])*w) for i in current}
                    if any(abs(targets[i]-current[i])>6 for i in current):raise RuntimeError('Restore step too large')
                    for sid in current:
                        err,data=bus.read(sid,0,66);check_identity(sid,err,data,cfg)
                        decode_and_check(sid,err,data,0,current)
                    bus.sync_write(42,2,[(i,targets[i].to_bytes(2,'little')) for i in sorted(targets)]);bus.ser.flush()
                    current=targets;result['events'].append({'frame':k,'targets':targets})
                    progress({'frame':k,'total':count,'phase':'SUPPORTED_SLOW_RESTORE','skipped':result['skipped']});time.sleep(.1)
                for sid in current:
                    err,data=bus.read(sid,0,66);check_identity(sid,err,data,cfg);decode_and_check(sid,err,data,0,start)
                result['status']='COMPLETE_SUPPORTED_RESTORE' if not result['skipped'] else 'PARTIAL_SUPPORTED_RESTORE'
            finally:bus.close()
    except BaseException as exc:result.update(status='STOPPED_LAST_GOAL_HELD_NO_AUTO_RETRY',failure=str(exc));raise
    finally:write_json(path,result)
    return {k:v for k,v in result.items() if k!='events'}|{'record':str(path)}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['plan','inspect','imu-check','capture','restore','run'])
    parser.add_argument('--robot');parser.add_argument('--parameters');parser.add_argument('--cycles',type=int,default=1,choices=[1,2,3,5])
    parser.add_argument('--output',default='.local/robot.json');parser.add_argument('--supported',action='store_true')
    parser.add_argument('--onsite-ready',action='store_true');parser.add_argument('--partial',action='store_true')
    parser.add_argument('--seconds',type=float,default=5.,help='Read-only imu-check duration, 1..60 seconds')
    args=parser.parse_args();cfg=read_json(args.robot) if args.robot else None
    params=read_json(args.parameters) if args.parameters else defaults()
    stop=threading.Event()
    signal.signal(signal.SIGINT,lambda *_:stop.set());signal.signal(signal.SIGTERM,lambda *_:stop.set())
    def cancel():
        if stop.is_set():raise RuntimeError('Operator stop')
    def report(row):print(json.dumps(row,ensure_ascii=False),flush=True)
    if args.action=='plan':report(plan(cfg,params,args.cycles));return
    if cfg is None:parser.error('--robot is required for serial access')
    if args.action=='imu-check':
        from imu_diagnostics import inspect_imu
        with ownership(cfg.get('imu_port',''),HERE/'.local/locks'):
            result=inspect_imu(cfg,args.seconds,report,cancel)
    elif args.action=='inspect':result=inspect_device(cfg)
    elif args.action=='capture':result=capture_start(cfg,args.output)
    elif args.action=='restore':
        if not args.supported:parser.error('Restore requires --supported and physical support/unloaded feet')
        print('Slow supported restore begins in 3 seconds. Ctrl+C cancels.',flush=True);time.sleep(3);cancel()
        result=restore(cfg,report,cancel,partial=args.partial)
    else:
        if not args.onsite_ready:parser.error('Run requires --onsite-ready and onsite support/catch preparation')
        print('D run: first 150 frames prepare; then motion. Ctrl+C stops targets, does not release torque.',flush=True)
        result=run(cfg,params,args.cycles,report,cancel)
    report(result)

if __name__=='__main__':main()
