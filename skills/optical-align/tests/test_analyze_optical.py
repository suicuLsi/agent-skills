import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image, ImageDraw, ImageFilter, ImageOps

spec = importlib.util.spec_from_file_location('optical', Path(__file__).parents[1] / 'scripts/analyze_optical.py')
optical = importlib.util.module_from_spec(spec)
spec.loader.exec_module(optical)


class OpticalTests(unittest.TestCase):
    def setUp(self):
        self.mask = Image.new('L', (80, 40))
        ImageDraw.Draw(self.mask).rectangle((30, 10, 49, 29), fill=255)

    def test_symmetric_mark_and_scale(self):
        result = optical.measure(self.mask, 2)
        self.assertEqual(result['bounds'], [15, 5, 25, 15])
        self.assertEqual(result['centroid'], [20, 10])
        self.assertEqual(result['centroid_minus_reference_center'], [0, 0])

    def test_known_shift_and_overflow(self):
        shifted = Image.new('L', self.mask.size)
        shifted.paste(self.mask, (4, -2))
        result = optical.measure(shifted, 2)
        self.assertEqual(result['centroid_minus_reference_center'], [2, -1])
        result = optical.measure(self.mask, 2, (35, 0, 80, 40))
        self.assertEqual(result['rectangular_gaps']['left'], -2.5)

    def test_centroid_is_not_bbox_center_for_asymmetric_icon(self):
        mask = Image.new('L', (80, 40))
        ImageDraw.Draw(mask).polygon([(20, 10), (20, 29), (59, 20)], fill=255)
        result = optical.measure(mask, 1)
        self.assertLess(result['centroid'][0], sum(result['bounds'][::2]) / 2 - 4)

    def test_light_dark_background_equivalence(self):
        light = Image.merge('RGB', (ImageOps.invert(self.mask),) * 3)
        dark = Image.merge('RGB', (self.mask,) * 3)
        a, _ = optical.foreground(light, '#ffffff')
        b, _ = optical.foreground(dark, '#000000')
        self.assertEqual(optical.measure(a, 1), optical.measure(b, 1))

    def test_alpha_and_supplied_mask(self):
        image = Image.new('RGBA', self.mask.size, '#ffffff')
        image.putalpha(self.mask)
        alpha, method = optical.foreground(image)
        self.assertEqual(method, 'alpha-coverage')
        self.assertEqual(optical.measure(alpha, 1), optical.measure(self.mask, 1))
        contextual = Image.new('RGB', self.mask.size, '#ab2c4d')
        supplied, _ = optical.foreground(contextual, mask=self.mask)
        self.assertEqual(optical.measure(supplied, 1), optical.measure(alpha, 1))
        with self.assertRaises(ValueError):
            optical.foreground(contextual)
        with self.assertRaises(ValueError):
            optical.foreground(contextual, mask=self.mask.convert('RGB'))
        with self.assertRaises(ValueError):
            optical.foreground(contextual, mask=Image.new('L', (10, 10)))

    def test_invalid_measurements_are_rejected(self):
        for scale in (0, -1, float('nan'), float('inf')):
            with self.subTest(scale=scale), self.assertRaises(ValueError):
                optical.measure(self.mask, scale)
        for rect in ((0, 0, 81, 40), (1, 1, 1, 10), (-1, 0, 10, 10)):
            with self.subTest(rect=rect), self.assertRaises(ValueError):
                optical.measure(self.mask, 1, rect)
        with self.assertRaises(ValueError):
            optical.measure(Image.new('L', self.mask.size), 1)

    def test_blur_preserves_symmetric_center_with_padding(self):
        blurred = ImageOps.expand(self.mask, 12).filter(ImageFilter.GaussianBlur(4))
        result = optical.measure(blurred, 1)
        self.assertEqual(result['centroid'], [52, 32])

    def test_cli_artifacts_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as root:
            image = Image.new('RGBA', self.mask.size, 'white')
            image.putalpha(self.mask)
            source = Path(root) / 'mark.png'
            image.save(source)
            out = Path(root) / 'diagnostics'
            args = ['analyze_optical.py', str(source), '--pixels-per-unit', '2', '--out', str(out)]
            with patch.object(sys, 'argv', args), contextlib.redirect_stdout(io.StringIO()):
                optical.main()
            report = json.loads((out / 'measurements.json').read_text())
            self.assertEqual(report['measurements']['centroid'], [20, 10])
            self.assertEqual(report['unit'], 'css-px')
            self.assertEqual(len(list(out.iterdir())), 9)
            with Image.open(out / 'original.png') as original:
                self.assertEqual(original.tobytes(), image.tobytes())
            before = (out / 'measurements.json').read_bytes()
            with patch.object(sys, 'argv', args), contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as caught:
                optical.main()
            self.assertEqual(caught.exception.code, 2)
            self.assertEqual(before, (out / 'measurements.json').read_bytes())

    def test_uncalibrated_unit_cannot_claim_scaled_pixels(self):
        args = ['analyze_optical.py', 'unused.png', '--unit', 'image-px', '--pixels-per-unit', '2', '--out', 'unused']
        with patch.object(sys, 'argv', args), contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as caught:
            optical.main()
        self.assertEqual(caught.exception.code, 2)

    def test_large_input_rejected_before_processing(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / 'large.png'
            Image.new('L', (1025, 1024)).save(path)
            with self.assertRaises(ValueError):
                optical.read_png(path)


if __name__ == '__main__':
    unittest.main()
