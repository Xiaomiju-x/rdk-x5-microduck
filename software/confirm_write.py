"""Resolve one ambiguous USB write by fresh full-bus target readback only.

Never resend automatically. Resume only if ALL15 are enabled with the exact
attempted goals (including unchanged mouth), valid positions and fault state.
An old/mixed target set, missing data, a second ambiguous write or slow readback
remains an error. This does not suppress a failed write or relax servo faults.
"""
import time
from feedback import decode_and_check


def confirm_position_write(bus,target,frame,events,error,clock=time.monotonic):
    if set(target)!=set(range(1,16)) or any(type(v) is not int or not 0<=v<=4095 for v in target.values()):
        raise ValueError('Full valid target set required')
    if events:
        raise RuntimeError('Only one ambiguous write confirmation per finite trial')
    entry=dict(frame=frame,write_exception=repr(error),attempted_targets=dict(target),
               status='READBACK_PENDING',automatic_resends=0)
    events.append(entry);begun=clock()
    try:
        rows=bus.sync_read(list(range(1,11)),40,26)
        for sid in range(11,16):rows[sid]=bus.read(sid,40,26)
        if set(rows)!=set(target) or any(v is None for v in rows.values()):
            raise RuntimeError('Incomplete ambiguous-write readback')
        entry['readback_state']={sid:decode_and_check(sid,*rows[sid],40,target) for sid in rows}
        elapsed=(clock()-begun)*1000
        if elapsed>60:
            raise RuntimeError('Ambiguous-write readback exceeded 60ms confirmation budget')
        entry.update(status='ALL15_EXACT_TARGETS_ENABLED_CONFIRMED_WITHOUT_RESEND',readback_ms=elapsed)
        return entry
    except BaseException as exc:
        entry.update(status='UNCONFIRMED_NO_RESEND',failure=repr(exc))
        raise
    finally:
        entry['total_readback_ms']=(clock()-begun)*1000
