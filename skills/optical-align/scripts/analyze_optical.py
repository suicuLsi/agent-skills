#!/usr/bin/env python3
"""Bounded foreground diagnostics; never infer or apply an optical correction."""

import argparse
import json
import math
import re
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageOps


MAX_PIXELS = 1_048_576
VISIBILITY = 16


def read_png(path):
    if path.stat().st_size > 16 * 1024 * 1024:
        raise ValueError('PNG exceeds 16 MiB; crop the component first')
    with Image.open(path) as source:
        if source.format != 'PNG' or getattr(source, 'n_frames', 1) != 1:
            raise ValueError('Expected a single-frame PNG')
        if source.width * source.height > MAX_PIXELS:
            raise ValueError('PNG exceeds 1,048,576 pixels; crop the component first')
        if source.getexif().get(274, 1) != 1:
            raise ValueError('Normalize image orientation and mask before analysis')
        return source.copy()


def foreground(image, background=None, mask=None):
    if mask is not None:
        if mask.mode != 'L' or mask.size != image.size:
            raise ValueError('Mask must be 8-bit grayscale (L), matching the image size')
        return mask.copy(), 'supplied-coverage-mask'
    rgba = image.convert('RGBA')
    alpha = rgba.getchannel('A')
    if background is None:
        if alpha.getextrema()[0] == 255:
            raise ValueError('Opaque image requires --background or --mask')
        return alpha, 'alpha-coverage'
    if not re.fullmatch(r'#[0-9a-fA-F]{6}', background):
        raise ValueError('Background must be #RRGGBB')
    base = Image.new('RGBA', rgba.size, background)
    rendered = Image.alpha_composite(base, rgba).convert('RGB')
    # shortcut: sRGB luminance difference is approximate; use a coverage mask for complex/color-sensitive cases.
    return ImageChops.difference(rendered, base.convert('RGB')).convert('L'), 'srgb-luminance-difference'


def measure(mask, scale, container=None):
    if not math.isfinite(scale) or scale <= 0:
        raise ValueError('Pixels per unit must be finite and greater than zero')
    width, height = mask.size
    rect = tuple(container) if container is not None else (0, 0, width, height)
    left, top, right, bottom = rect
    if not all(math.isfinite(v) for v in rect) or not (0 <= left < right <= width and 0 <= top < bottom <= height):
        raise ValueError('Container must be a nonempty rectangle inside the crop')
    weights = mask.point([value if value >= VISIBILITY else 0 for value in range(256)])
    bounds = weights.getbbox()
    if bounds is None:
        raise ValueError('No foreground at the 16/255 visibility threshold')
    mass = mx = my = 0.0
    for index, weight in enumerate(weights.tobytes()):
        if weight:
            mass += weight
            mx += (index % width + .5) * weight
            my += (index // width + .5) * weight
    cx, cy = mx / mass, my / mass
    x0, y0, x1, y1 = bounds
    return {
        'bounds': [v / scale for v in bounds],
        'centroid': [cx / scale, cy / scale],
        'reference_rect': [v / scale for v in rect],
        'centroid_minus_reference_center': [(cx - (left + right) / 2) / scale, (cy - (top + bottom) / 2) / scale],
        'rectangular_gaps': dict(zip(('left', 'top', 'right', 'bottom'),
                                    [(x0 - left) / scale, (y0 - top) / scale, (right - x1) / scale, (bottom - y1) / scale])),
    }


def write_diagnostics(image, mask, metrics, scale, background, out):
    rgba = image.convert('RGBA')
    preview = Image.alpha_composite(Image.new('RGBA', rgba.size, background or '#808080'), rgba).convert('RGB')
    x0, y0, x1, y1 = [value * scale for value in metrics['bounds']]
    short_side = min(x1 - x0, y1 - y0)
    sigmas = [max(.5, short_side / 12), max(1, short_side / 4)]
    padding = math.ceil(3 * sigmas[-1])
    padded = ImageOps.expand(mask, padding, fill=0)
    blurs = [padded.filter(ImageFilter.GaussianBlur(sigma)) for sigma in sigmas]
    context_blurs = [preview.filter(ImageFilter.GaussianBlur(sigma)) for sigma in sigmas]
    guided = preview.copy()
    draw = ImageDraw.Draw(guided)
    l, t, r, b = [value * scale for value in metrics['reference_rect']]
    draw.rectangle((l, t, max(l, r - 1), max(t, b - 1)), outline='#00aaff')
    draw.rectangle((x0, y0, x1 - 1, y1 - 1), outline='#ff9900')
    for (x, y), color in [(((l + r) / 2, (t + b) / 2), '#00aaff'),
                          (tuple(v * scale for v in metrics['centroid']), '#ff3366')]:
        draw.line((x - 4, y, x + 4, y), fill=color)
        draw.line((x, y - 4, x, y + 4), fill=color)
    panels = [('Source (alpha on gray)' if background is None and rgba.getchannel('A').getextrema()[0] < 255 else 'Source', preview),
              ('Foreground weights', mask), ('Guides: box / ink / centroid', guided),
              ('Whole scene: light blur', context_blurs[0]), ('Whole scene: strong blur', context_blurs[1])]
    cell_width, cell_height = 360, 300
    sheet = Image.new('RGB', (cell_width * 3, cell_height * 2), '#eeeeee')
    sheet_draw = ImageDraw.Draw(sheet)
    for index, (label, panel) in enumerate(panels):
        thumb = panel.convert('RGB')
        thumb.thumbnail((cell_width - 16, cell_height - 40))
        x, y = index % 3 * cell_width, index // 3 * cell_height
        sheet_draw.text((x + 8, y + 8), label, fill='#111111')
        sheet.paste(thumb, (x + (cell_width - thumb.width) // 2, y + 32))
    sheet_draw.text((728, 308), 'Diagnostics only.\nReview the real UI at 100%.\nOffsets are not recommendations.', fill='#111111', spacing=8)
    out.mkdir(parents=True, exist_ok=False)
    image.save(out / 'original.png')
    mask.save(out / 'mask.png')
    guided.save(out / 'guided.png')
    for name, blurred in zip(('blur-light.png', 'blur-strong.png'), blurs):
        blurred.save(out / name)
    for name, blurred in zip(('context-blur-light.png', 'context-blur-strong.png'), context_blurs):
        blurred.save(out / name)
    sheet.save(out / 'comparison.png')
    return {'sigma_image_px': sigmas, 'mask_padding_image_px': padding, 'context_blurs': 'Whole captured scene, including container and other content'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('image', type=Path)
    source = parser.add_mutually_exclusive_group()
    source.add_argument('--background', help='Uniform background #RRGGBB')
    source.add_argument('--mask', type=Path, help='Matching grayscale coverage PNG')
    parser.add_argument('--pixels-per-unit', type=float, required=True)
    parser.add_argument('--unit', choices=('css-px', 'pt', 'image-px'), default='css-px')
    parser.add_argument('--container', type=float, nargs=4, metavar=('LEFT', 'TOP', 'RIGHT', 'BOTTOM'))
    parser.add_argument('--out', type=Path, required=True, help='New output directory; never overwritten')
    args = parser.parse_args()
    try:
        if args.unit == 'image-px' and args.pixels_per_unit != 1:
            raise ValueError('Uncalibrated image-px measurements require --pixels-per-unit 1')
        image = read_png(args.image)
        supplied = read_png(args.mask) if args.mask else None
        mask, method = foreground(image, args.background, supplied)
        metrics = measure(mask, args.pixels_per_unit, args.container)
        blur = write_diagnostics(image, mask, metrics, args.pixels_per_unit, args.background, args.out)
        report = {
            'unit': args.unit, 'pixels_per_unit': args.pixels_per_unit,
            'image_size_px': list(image.size), 'foreground_method': method,
            'visibility_threshold': VISIBILITY, 'measurements': metrics, 'blur': blur,
            'interpretation': 'Rectangular gaps and weighted centroid only; not optical correction, curved spacing, or baseline measurements.',
        }
        (args.out / 'measurements.json').write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
    except (OSError, ValueError, Image.DecompressionBombError) as error:
        parser.exit(2, f'error: {error}\n')
    print(args.out / 'measurements.json')


if __name__ == '__main__':
    main()
