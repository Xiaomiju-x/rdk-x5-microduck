"""Passive JY901S trace on its own port/thread; no configuration writes.

Angle/gyro decoding matches the inspected hip_probe_20260926.py. Values are in
the SENSOR frame, not a newly calibrated body/COM estimate. Not a balance loop.
"""
import struct
import threading
import time

PORT='/dev/serial/by-id/SELECT_IMU_ADAPTER'


class Parser:
    def __init__(self):self.buffer=bytearray();self.bad=0
    def feed(self,data,stamp):
        self.buffer.extend(data);out=[]
        while len(self.buffer)>=11:
            if self.buffer[0]!=0x55:del self.buffer[0];continue
            if sum(self.buffer[:10])%256!=self.buffer[10]:
                self.bad+=1;del self.buffer[0];continue
            frame=bytes(self.buffer[:11]);del self.buffer[:11]
            xyz=struct.unpack('<hhh',frame[2:8])
            row=dict(mono_s=stamp,kind=frame[1],raw_xyz=xyz)
            if frame[1]==0x53:row['sensor_angles_deg']=[v*180/32768 for v in xyz]
            if frame[1]==0x52:row['sensor_gyro_dps']=[v*2000/32768 for v in xyz]
            out.append(row)
        return out


class ImuTrace:
    def __init__(self):
        self.parser=Parser();self.records=[];self.latest={};self.error=None
        self.done=threading.Event();self.thread=None;self.port=None
    def start(self):
        import serial
        self.port=serial.Serial(PORT,115200,timeout=.01,exclusive=True)
        self.port.reset_input_buffer()
        self.thread=threading.Thread(target=self._run,daemon=True)
        self.thread.start()
        deadline=time.monotonic()+1.5
        while time.monotonic()<deadline:
            if self.error:raise RuntimeError('IMU trace failed: '+self.error)
            if sum(r['kind']==0x53 for r in self.records)>=5 and 0x52 in self.latest:return
            time.sleep(.01)
        raise RuntimeError('No valid IMU baseline; no motion should be started')
    def _run(self):
        try:
            while not self.done.is_set():
                rows=self.parser.feed(self.port.read(max(1,self.port.in_waiting)),time.monotonic())
                for row in rows:self.latest[row['kind']]=row;self.records.append(row)
        except Exception as exc:
            if not self.done.is_set():self.error=repr(exc)
    def snapshot(self):
        row=self.latest.get(0x53)
        if not row:return None
        return dict(sensor_angles_deg=list(row['sensor_angles_deg']),
                    host_age_ms=(time.monotonic()-row['mono_s'])*1000,error=self.error)
    def stop(self):
        self.done.set()
        if self.thread:self.thread.join(.3)
        if self.port:self.port.close()
        if self.thread and self.thread.is_alive():self.thread.join(.3)
        return dict(records=self.records,bad_checksum=self.parser.bad,error=self.error,
                    thread_stopped=self.thread is None or not self.thread.is_alive(),
                    mode='PASSIVE_SENSOR_TRACE_NOT_BALANCE_FEEDBACK',configuration_writes=0)
