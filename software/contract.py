"""D's existing actuator envelope, unchanged by public packaging."""
IDS=(1,2,3,4,5,11,12,13,14,6,7,8,9,10)
ALL_IDS=tuple(range(1,16))
CAP_DEG={1:10,2:10,3:15,4:22,5:20,6:10,7:10,8:15,9:22,10:15,11:10,12:10,13:10,14:10}
SLEW_COUNTS={i:(5 if i in (1,6,11,12,13,14) else 18) for i in IDS}

def check_target(target,start,previous,neck_extra_deg=0.,neck_front_extra_deg=0.):
    if set(target)!=set(start) or target[15]!=start[15]:
        raise ValueError('Full15 targets and fixed mouth required')
    for i in IDS:
        if type(target[i]) is not int or not 0<=target[i]<=4095:
            raise ValueError('Invalid encoder goal')
        cap=CAP_DEG[i]+(neck_extra_deg if i==11 else 0.)
        front_cap=cap+(neck_front_extra_deg if i==11 else 0.)
        if not -round(front_cap*4096/360)<=target[i]-start[i]<=round(cap*4096/360):
            raise ValueError('Amplitude outside existing D envelope')
        if abs(target[i]-previous[i])>SLEW_COUNTS[i]:
            raise ValueError('Slew outside existing D envelope')

def position_packet(target,ids=IDS):
    args=bytes([42,2])+b''.join(bytes([i,target[i]&255,target[i]>>8]) for i in sorted(ids))
    body=bytes([254,len(args)+2,0x83])+args
    return b'\xff\xff'+body+bytes([255-sum(body)%256])

class PositionGuard:
    """READ plus exactly the armed goal packet; no EEPROM/PD/unload commands."""
    def __init__(self,raw,start,parameters):
        self.raw=raw;self.start=dict(start);self.last=dict(start)
        self.allowed=None;self.writes=0
        self.extra=8. if parameters['neck_mode']=='legacy_offset' and (parameters['bias_deg'] or parameters['back_gain']) else 0.
        self.front=20. if parameters['neck_mode']=='two_stage_pose' else 0.
    def write(self,p):
        if len(p)<6 or p[:2]!=b'\xff\xff' or len(p)!=p[3]+4 or sum(p[2:])%256!=255:
            raise ValueError('Malformed packet')
        sid,op,args=p[2],p[4],p[5:-1]
        read=op==2 and 1<=sid<=15 and args in (bytes([0,66]),bytes([40,26]))
        sync=op==0x82 and sid==254 and args==bytes([40,26]+list(range(1,11)))
        if not (read or sync):
            if self.allowed is None:raise ValueError('No armed position frame')
            check_target(self.allowed,self.start,self.last,self.extra,self.front)
            if p!=position_packet(self.allowed):raise ValueError('Only armed position frame allowed')
            self.last=dict(self.allowed);self.allowed=None;self.writes+=1
        n=self.raw.write(p)
        if n!=len(p):raise IOError('Partial write')
        return n
    def __getattr__(self,key):return getattr(self.raw,key)
