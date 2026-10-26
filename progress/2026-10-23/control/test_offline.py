import json
import unittest
from pathlib import Path
from duck_tuning_config_20260929 import validate_parameters, DEFAULTS
from neck_prefix_compensation_20260929 import NeckPrefixCompensation


class OnboardPresetTests(unittest.TestCase):
    def test_frozen_sequence(self):
        p = json.loads((Path(__file__).resolve().parents[1] / 'parameters.json').read_text(encoding='utf8'))['parameters']
        self.assertEqual(validate_parameters(p)['return_advance_s'], 1.1)
        controller = NeckPrefixCompensation(parameters=p)
        start = {i: 2048 for i in range(1, 16)}
        previous = dict(start)
        for frame in range(400):
            base = {i: start[i] + (frame % 3 if 150 <= frame < 250 else 0) for i in start}
            target, info = controller.apply(frame, 0., base, start, previous)
            self.assertLessEqual(abs(target[11] - previous[11]), 5)
            self.assertEqual({i: target[i] for i in start if i != 11}, {i: base[i] for i in start if i != 11})
            if frame == 195:
                self.assertEqual(info['neck_stage'], 'RETURN_START')
            if frame >= 294:
                self.assertEqual(target[11], start[11])
            previous = target
        self.assertEqual(previous, start)

    def test_old_records_keep_zero_advance(self):
        old = {k:v for k,v in DEFAULTS.items() if k != 'return_advance_s'}
        self.assertEqual(validate_parameters(old)['return_advance_s'], 0.)

    def test_bad_values_are_rejected(self):
        for value in (-.1, 1.6, float('nan')):
            with self.assertRaises(ValueError):
                validate_parameters({**DEFAULTS, 'return_advance_s':value})


if __name__ == '__main__':
    unittest.main()
