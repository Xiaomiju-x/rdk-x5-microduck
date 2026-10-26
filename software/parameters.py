"""Shared, hardware-free validation for the local MicroDuck tuning panel."""
import math

LEGACY_KEYS={'gain','max_back_deg','deadband_deg'}
BIDIRECTIONAL_KEYS=LEGACY_KEYS|{'bias_deg','back_gain','max_front_deg'}
DEFAULTS={'gain':.325,'max_back_deg':4.,'deadband_deg':1.,
          'bias_deg':0.,'back_gain':0.,'max_front_deg':4.,
          'motion_deg':0.,'start_hold_s':.15,'transition_s':.6,'return_advance_s':0.,'neck_mode':'legacy_offset'}
LIMITS={'gain':(0.,.65),'max_back_deg':(0.,8.),'deadband_deg':(0.,3.),
        'bias_deg':(-8.,8.),'back_gain':(0.,.65),'max_front_deg':(0.,8.),
        'motion_deg':(-30.,8.),'start_hold_s':(0.,.8),'transition_s':(.2,1.5),'return_advance_s':(0.,1.5)}
OUTCOMES=('unreviewed','stable_forward','forward_fall','backward_fall','side_fall','no_forward')
WEIGHT_POSITIONS=('unchanged','front','rear','both','none')
CYCLE_CHOICES=(1,2,3,5)


def validate_cycles(value):
    """Run length is separate from the immutable per-cycle neck preset."""
    if type(value) is not int or value not in CYCLE_CHOICES:
        raise ValueError('D轮数只能选择1、2、3、5轮')
    return value


def validate_parameters(value):
    if not isinstance(value,dict) or set(value) not in (LEGACY_KEYS,BIDIRECTIONAL_KEYS,set(DEFAULTS)-{'return_advance_s'},set(DEFAULTS)):
        raise ValueError('D参数格式错误，请刷新面板')
    value={**DEFAULTS,**value}  # Old logs/presets retain their exact behavior.
    if value['neck_mode'] not in ('legacy_offset','two_stage_pose'):raise ValueError('颈部模式无效')
    result={}
    for key,(lo,hi) in LIMITS.items():
        v=value[key]
        if type(v) not in (int,float) or not math.isfinite(v) or not lo<=v<=hi:
            raise ValueError(f'{key} 必须在 {lo}～{hi} 之间')
        result[key]=float(v)
    result['neck_mode']=value['neck_mode']
    return result


def validate_ballast(value):
    if not isinstance(value,dict) or set(value)!={'position','note'}:
        raise ValueError('配重记录格式错误')
    if value['position'] not in WEIGHT_POSITIONS or not isinstance(value['note'],str) or len(value['note'])>300:
        raise ValueError('配重位置或备注无效（备注最多300字）')
    return dict(value)
