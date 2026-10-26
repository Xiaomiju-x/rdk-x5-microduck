"""Original D feedback validation, extracted without changes."""
def decode_and_check(sid,error,data,origin,expected):
    def b(a):return data[a-origin]
    def w(a):return b(a)+256*b(a+1)
    raw=w(56)
    state=dict(torque=b(40),target=w(42),pos=-(raw&32767) if raw&32768 else raw,
               voltage=b(62)/10,temp=b(63),error=b(65))
    # Bit0 is the manufacturer's voltage status. Under-voltage alone is the
    # requested log-only observation, not a second hidden abort path.
    if (error & ~1) or (state['error'] & ~1) or state['torque']!=1 or state['target']!=expected[sid]:
        raise RuntimeError('Servo fault/reset/target mismatch '+str((sid,state)))
    if not 0<=state['pos']<=4095 or not 0<state['voltage']<=8.4:
        raise RuntimeError('Invalid feedback/overvoltage '+str((sid,state)))
    # Deliberately NO voltage >=4 gate and NO position-error abort gate.
    state['tracking_error_counts']=state['pos']-state['target']
    state['low_voltage_observation']=state['voltage']<4
    state['voltage_status_observation']=bool((error|state['error'])&1)
    state['ordinary_lag_observation']=abs(state['tracking_error_counts'])>35
    state['temperature_observation']=state['temp']>55
    return state
