"""Shared, hardware-free validation for the local MicroDuck tuning panel."""
import math

DEFAULTS={'gain':.325,'max_back_deg':4.,'deadband_deg':1.}
LIMITS={'gain':(0.,.65),'max_back_deg':(0.,8.),'deadband_deg':(0.,3.)}
OUTCOMES=('unreviewed','stable_forward','forward_fall','backward_fall','side_fall','no_forward')
WEIGHT_POSITIONS=('unchanged','front','rear','both','none')


def validate_parameters(value):
    if not isinstance(value,dict) or set(value)!=set(DEFAULTS):
        raise ValueError('参数只允许 gain、max_back_deg、deadband_deg')
    result={}
    for key,(lo,hi) in LIMITS.items():
        v=value[key]
        if type(v) not in (int,float) or not math.isfinite(v) or not lo<=v<=hi:
            raise ValueError(f'{key} 必须在 {lo}～{hi} 之间')
        result[key]=float(v)
    return result


def validate_ballast(value):
    if not isinstance(value,dict) or set(value)!={'position','note'}:
        raise ValueError('配重记录格式错误')
    if value['position'] not in WEIGHT_POSITIONS or not isinstance(value['note'],str) or len(value['note'])>300:
        raise ValueError('配重位置或备注无效（备注最多300字）')
    return dict(value)
