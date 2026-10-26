"""At most one fresh head READ retry per tick, at most three per finite trial.

The inspected bus's receive timeout is handled. An explicitly supplied serial
write-timeout class additionally permits retrying this READ request, never a
motion write. That recovery must finish within 80 ms of the first attempt.
No cached feedback, torque/config writes, checksum/status suppression, or loop.
The caller must still validate reset/target/voltage/fault bits normally.
"""
import time


class BoundedHeadRead:
    def __init__(self,bus,timeout_type,read_write_timeout_type=None):
        if not isinstance(timeout_type,type) or not issubclass(timeout_type,Exception):
            raise ValueError('Specific bus timeout class required')
        if read_write_timeout_type is not None and (
                not isinstance(read_write_timeout_type,type)
                or not issubclass(read_write_timeout_type,Exception)):
            raise ValueError('Specific optional serial write timeout class required')
        self.bus=bus
        self.timeout_type=timeout_type
        self.read_write_timeout_type=read_write_timeout_type
        self.retry_types=(timeout_type,) if read_write_timeout_type is None else (timeout_type,read_write_timeout_type)
        self.events=[]
        self.last_retry_frame=None

    def read(self,sid,frame):
        if sid not in range(11,16) or type(frame) is not int or frame<0:
            raise ValueError('Fresh head feedback only')
        first_started=time.monotonic()
        try:
            return self.bus.read(sid,40,26)
        except self.retry_types as exc:
            if self.last_retry_frame==frame or len(self.events)>=3:
                raise
            read_write_timeout=(self.read_write_timeout_type is not None
                                and isinstance(exc,self.read_write_timeout_type))
            self.last_retry_frame=frame
            event=dict(frame=frame,id=sid,first_timeout=repr(exc),recovered=False,
                first_failure_kind='READ_REQUEST_WRITE_TIMEOUT' if read_write_timeout else 'REPLY_TIMEOUT',
                first_attempt_ms=(time.monotonic()-first_started)*1000)
            self.events.append(event)
            if read_write_timeout and time.monotonic()-first_started>=.08:
                event['retry_not_attempted']='80ms total read recovery budget already exhausted'
                raise
            start=time.monotonic()
            try:
                # FeetechBus.read clears its RX buffer before a new request.
                # No position packet is sent between these two read attempts.
                # Repeating a READ is idempotent even if the first READ reached
                # the device despite a host-side write timeout. Do not purge TX.
                row=self.bus.read(sid,40,26)
                if read_write_timeout and time.monotonic()-first_started>.08:
                    raise TimeoutError('READ request recovery exceeded 80ms; do not use late feedback')
            except BaseException as retry_exc:
                event['retry_failure']=repr(retry_exc)
                raise
            else:
                event['recovered']=True
                return row
            finally:
                event['retry_read_ms']=(time.monotonic()-start)*1000
                event['total_read_ms']=(time.monotonic()-first_started)*1000
