"""Finite relative-pitch neck correction for a recorded-goal experiment.

ID11 raw+ was physically confirmed to move the neck backward. Only this one
axis may differ from the pinned sent-target prefix. Sensor reference is an
in-memory change reference, NOT IMU zeroing or a saved body-frame calibration.
"""
import math
import statistics
from live_policy_air_preview_20260928 import CAP_DEG,SLEW_COUNTS


class NeckPrefixCompensation:
    max_back_deg=8.
    gain=.65
    deadband_deg=1.
    offset_slew_counts=3

    def __init__(self,correction_scale=1.,parameters=None):
        if correction_scale not in (.5,1.):
            raise ValueError('Only original or explicitly halved compensation is supported')
        self.correction_scale=float(correction_scale)
        self.gain=type(self).gain*self.correction_scale
        self.max_back_deg=type(self).max_back_deg*self.correction_scale
        if parameters is not None:
            if correction_scale!=1.:raise ValueError('Choose a scale or explicit parameters, not both')
            from duck_tuning_config_20260929 import validate_parameters
            config=validate_parameters(parameters)
            self.gain=config['gain'];self.max_back_deg=config['max_back_deg']
            self.deadband_deg=config['deadband_deg']
            self.correction_scale=None
        self.baseline_samples=[]
        self.reference=None
        self.applied_offset=0
        self.return_offset=None

    def apply(self,frame,pitch_deg,base,start,previous):
        if not 0<=frame<400 or not math.isfinite(pitch_deg):
            raise ValueError('Finite 400-frame compensated experiment only')
        target=dict(base)
        error=None
        if frame<150:
            self.baseline_samples.append(float(pitch_deg))
            self.baseline_samples=self.baseline_samples[-50:]
            requested_offset=0
        elif frame<250:
            if self.reference is None:
                if len(self.baseline_samples)!=50:raise ValueError('No stationary pitch reference')
                self.reference=statistics.median(self.baseline_samples)
            error=pitch_deg-self.reference
            requested_deg=min(self.max_back_deg,self.gain*max(0.,error-self.deadband_deg))
            desired=round(requested_deg*4096/360)
            requested_offset=max(self.applied_offset-self.offset_slew_counts,
                                 min(self.applied_offset+self.offset_slew_counts,desired))
        elif frame<350:
            if self.return_offset is None:self.return_offset=self.applied_offset
            u=(frame-249)/100
            requested_offset=round(self.return_offset*(1-u*u*(3-2*u)))
        else:
            requested_offset=0
        desired_target=base[11]+requested_offset
        cap=round(CAP_DEG[11]*4096/360)
        desired_target=min(start[11]+cap,max(start[11]-cap,desired_target))
        target[11]=max(previous[11]-SLEW_COUNTS[11],
                       min(previous[11]+SLEW_COUNTS[11],desired_target))
        offset=target[11]-base[11]
        if not 0<=offset<=round(self.max_back_deg*4096/360):
            raise ValueError('Correction must only reduce forward neck motion')
        if frame>=350 and target[11]!=start[11]:raise ValueError('Neck must finish exactly at saved R3')
        self.applied_offset=offset
        return target,dict(reference_candidate_pitch_deg=self.reference,
            correction_scale=self.correction_scale,gain=self.gain,
            max_back_deg=self.max_back_deg,deadband_deg=self.deadband_deg,
            candidate_pitch_deg=pitch_deg,forward_change_deg=error,
            requested_offset_counts=requested_offset,applied_back_offset_counts=offset,
            applied_back_offset_deg=offset*360/4096,
            source_neck_goal=base[11],corrected_neck_goal=target[11],
            raw_increase_verified_direction='NECK_BACKWARD',
            all_other_targets_unchanged=True)
