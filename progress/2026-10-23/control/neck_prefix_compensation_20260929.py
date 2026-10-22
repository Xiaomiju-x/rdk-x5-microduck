"""Finite relative-pitch neck correction for a recorded-goal experiment.

ID11 raw+ was physically confirmed to move the neck backward. Only this one
axis may differ from the pinned sent-target prefix. Sensor reference is an
in-memory change reference, NOT IMU zeroing or a saved body-frame calibration.
"""
import math
import statistics
# Public hardware-free extract: only these ID11 constants are used here.
# The internal module imported them from a hardware runtime; no runtime is
# imported or distributed by this standalone controller example.
CAP_DEG={11:10}
SLEW_COUNTS={11:5}


class NeckPrefixCompensation:
    max_back_deg=8.
    gain=.65
    deadband_deg=1.
    offset_slew_counts=3
    bias_deg=0.
    back_gain=0.
    max_front_deg=4.
    neck_mode='legacy_offset'
    motion_deg=0.
    start_hold_s=.15
    transition_s=.6
    return_advance_s=0.

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
            self.bias_deg=config['bias_deg'];self.back_gain=config['back_gain']
            self.max_front_deg=config['max_front_deg']
            self.neck_mode=config['neck_mode'];self.motion_deg=config['motion_deg']
            self.start_hold_s=config['start_hold_s'];self.transition_s=config['transition_s']
            self.return_advance_s=config['return_advance_s']
            self.correction_scale=None
        self.baseline_samples=[]
        self.reference=None
        self.applied_offset=0
        self.return_offset=None
        self.return_neck_target=None

    def apply(self,frame,pitch_deg,base,start,previous,motion_elapsed_s=None):
        if not 0<=frame<400 or not math.isfinite(pitch_deg):
            raise ValueError('Finite 400-frame compensated experiment only')
        if self.neck_mode=='two_stage_pose':
            return self.apply_staged(frame,pitch_deg,base,start,previous,motion_elapsed_s)
        target=dict(base)
        error=None
        requested_deg=0.
        feedback_deg=0.
        if frame<150:
            self.baseline_samples.append(float(pitch_deg))
            self.baseline_samples=self.baseline_samples[-50:]
            # Last second of preparation gently introduces the fixed neck bias.
            # Zero bias preserves every historical target and its timing.
            u=max(0.,min(1.,(frame-99)/50))
            requested_deg=self.bias_deg*u*u*(3-2*u)
            requested_offset=round(requested_deg*4096/360)
        elif frame<250:
            if self.reference is None:
                if len(self.baseline_samples)!=50:raise ValueError('No stationary pitch reference')
                self.reference=statistics.median(self.baseline_samples)
            error=pitch_deg-self.reference
            feedback_deg=(min(self.max_back_deg,self.gain*max(0.,error-self.deadband_deg))
                -min(self.max_front_deg,self.back_gain*max(0.,-error-self.deadband_deg)))
            requested_deg=max(-8.,min(8.,self.bias_deg+feedback_deg))
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
        # Only the explicitly selected new bidirectional mode needs room for
        # the original neck trajectory PLUS an 8deg offset. Legs are untouched.
        extra=8. if self.bias_deg or self.back_gain else 0.
        cap=round((CAP_DEG[11]+extra)*4096/360)
        desired_target=min(start[11]+cap,max(start[11]-cap,desired_target))
        target[11]=max(previous[11]-SLEW_COUNTS[11],
                       min(previous[11]+SLEW_COUNTS[11],desired_target))
        offset=target[11]-base[11]
        if abs(offset)>round(8.*4096/360):
            raise ValueError('Combined neck correction exceeds 8 degrees')
        if frame>=350 and target[11]!=start[11]:raise ValueError('Neck must finish exactly at saved R3')
        self.applied_offset=offset
        return target,dict(reference_candidate_pitch_deg=self.reference,
            correction_scale=self.correction_scale,gain=self.gain,
            max_back_deg=self.max_back_deg,deadband_deg=self.deadband_deg,
            bias_deg=self.bias_deg,back_gain=self.back_gain,max_front_deg=self.max_front_deg,
            feedback_deg=feedback_deg,requested_total_deg=requested_deg,
            signed_offset_deg=offset*360/4096,
            version='D_NECK_BIDIRECTIONAL_20261022',
            candidate_pitch_deg=pitch_deg,forward_change_deg=error,
            requested_offset_counts=requested_offset,applied_back_offset_counts=offset,
            applied_back_offset_deg=offset*360/4096,
            source_neck_goal=base[11],corrected_neck_goal=target[11],
            raw_increase_verified_direction='NECK_BACKWARD',
            all_other_targets_unchanged=True)

    def apply_staged(self,frame,pitch_deg,base,start,previous,motion_elapsed_s):
        """Absolute ID11 pose relative to START; zero really means START.

        Other fourteen axes and the original frame schedule are unchanged.
        Runtime supplies elapsed monotonic seconds since the first leg-motion
        frame; the frame-based fallback is for deterministic offline checks.
        """
        smooth=lambda u:max(0.,min(1.,u))**2*(3-2*max(0.,min(1.,u)))
        target=dict(base);error=None;feedback=0.;elapsed=None
        # Move the existing smooth return earlier on the unchanged leg timeline.
        # Seconds are nominal trajectory time (50 Hz), not a wall-clock deadline.
        return_frame=250-round(self.return_advance_s/.02)
        if frame<150:
            # Observe the initial body pose before moving the neck.
            if frame<100:
                self.baseline_samples.append(float(pitch_deg))
                self.baseline_samples=self.baseline_samples[-50:]
            requested_angle=self.bias_deg*smooth((frame-99)/50)
            stage='PREPARE' if frame<100 else 'START_BIAS'
            goal=start[11]+round(requested_angle*4096/360)
        elif frame<return_frame:
            elapsed=(frame-150)*.02 if motion_elapsed_s is None else motion_elapsed_s
            if not math.isfinite(elapsed) or elapsed<0:raise ValueError('Invalid motion clock')
            weight=smooth((elapsed-self.start_hold_s)/self.transition_s)
            requested_angle=self.bias_deg+(self.motion_deg-self.bias_deg)*weight
            stage='START_HOLD' if elapsed<self.start_hold_s else ('MOVE_BLEND' if weight<1 else 'MOVE_HOLD')
            if self.reference is None:
                if len(self.baseline_samples)!=50:raise ValueError('No initial pitch reference')
                self.reference=statistics.median(self.baseline_samples)
            error=pitch_deg-self.reference
            feedback=(min(self.max_back_deg,self.gain*max(0.,error-self.deadband_deg))
                     -min(self.max_front_deg,self.back_gain*max(0.,-error-self.deadband_deg)))
            requested_angle=max(-30.,min(8.,requested_angle+feedback))
            goal=start[11]+round(requested_angle*4096/360)
        elif frame<return_frame+100:
            if self.return_neck_target is None:self.return_neck_target=previous[11]
            goal=round(self.return_neck_target+(start[11]-self.return_neck_target)*smooth((frame-return_frame+1)/100))
            requested_angle=(goal-start[11])*360/4096;stage='RETURN_START'
        else:
            goal=start[11];requested_angle=0.;stage='FINAL_HOLD'
        target[11]=max(previous[11]-SLEW_COUNTS[11],min(previous[11]+SLEW_COUNTS[11],goal))
        if not 0<=target[11]<=4095 or not -round(30*4096/360)<=target[11]-start[11]<=round(8*4096/360):
            raise ValueError('Staged neck outside absolute START -30/+8deg')
        if frame>=350 and target[11]!=start[11]:raise ValueError('Neck did not finish at START')
        applied=(target[11]-start[11])*360/4096
        self.applied_offset=target[11]-base[11]
        return target,dict(version='D_NECK_EARLY_RETURN_20261023',neck_mode=self.neck_mode,
            neck_stage=stage,motion_elapsed_s=elapsed,angle_reference='SAVED_TEMP_START',
            bias_deg=self.bias_deg,motion_deg=self.motion_deg,start_hold_s=self.start_hold_s,
            transition_s=self.transition_s,return_advance_s=self.return_advance_s,
            return_start_frame=return_frame,requested_total_deg=requested_angle,
            applied_neck_angle_deg=applied,feedback_deg=feedback,
            reference_candidate_pitch_deg=self.reference,candidate_pitch_deg=pitch_deg,forward_change_deg=error,
            gain=self.gain,back_gain=self.back_gain,max_back_deg=self.max_back_deg,
            max_front_deg=self.max_front_deg,deadband_deg=self.deadband_deg,
            signed_offset_deg=self.applied_offset*360/4096,
            applied_back_offset_deg=applied,applied_back_offset_counts=target[11]-start[11],
            source_neck_goal=base[11],corrected_neck_goal=target[11],
            raw_increase_verified_direction='NECK_BACKWARD',all_other_targets_unchanged=True)
