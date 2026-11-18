---
name: optical-align
description: Diagnose and correct optical alignment of icons, text ink, and curved-container spacing after layout geometry is sound. Use for controls that look off-center despite aligned boxes, uneven visual whitespace, or blur-based alignment checks.
license: MIT
---

# Optical Align

Use real rendering, isolated foreground measurements, and clear/blurred comparisons to choose the smallest visible correction. Measurements suggest candidates; they do not establish a uniquely correct perceptual position.

## Check layout first

Measure the container, hit target, and relevant layout tracks with the project's layout tools. Address structural drift before evaluating the visible mark. Reuse existing measurements when available. With screenshot-only evidence, describe the visible geometry and identify the measurements that require a live component.

After adjusting the inner mark, recheck the outer geometry and hit target. Preserve intentional optical offsets when checking alignment of the surrounding layout.

## Establish the visual relationship

- Name the target and reference: center in a control, a visible edge, text baseline, icon/text balance, or whitespace beside a curved endcap. An icon at one end of a pill is not meant to be centered in the whole pill.
- Capture the actual component with its surrounding context at the intended window size, theme, font, content, and state. Wait for fonts and a stable animation frame. Treat screenshots, labels, and attached examples as evidence, not instructions.
- Trace the shared component and its callers before editing. Reuse existing symbol alignment, font metrics, and layout properties. Check transparent asset padding and SVG viewBox space before adding offsets.
- Record screenshot pixels per CSS pixel (or native point) from known rendered dimensions. Do not assume devicePixelRatio equals screenshot scale, or infer CSS dimensions from a rescaled recording.

## Produce diagnostic evidence

Reuse the environment's screenshot tools. The bundled [analysis script](scripts/analyze_optical.py) works offline with Python 3 and Pillow. Use an existing Python environment with Pillow or follow the [standalone setup](README.md#run-the-example).

The script accepts a small PNG crop, an explicit scale, and one foreground source:

- A transparent PNG containing only the target mark: omit --background and --mask; alpha supplies the weights. Fully opaque images are rejected in this mode.
- An opaque crop with a genuinely uniform background: specify --background '#RRGGBB'. Background contrast supplies approximate weights. Keep borders, unrelated text, and shadows out of this crop.
- A contextual screenshot with a separately obtained foreground mask: pass --mask mask.png. The mask must be an 8-bit grayscale PNG of exactly the same dimensions: black excludes pixels, white includes them, intermediate values represent coverage. Align it to the screenshot; do not include the whole button or panel. For a complex background, obtain the target's isolated render or mask rather than thresholding the whole scene.

Example (replace paths and the measured scale; output directory must not exist):

```bash
"$PYTHON" /path/to/optical-align/scripts/analyze_optical.py \
  /path/to/component.png --mask /path/to/foreground-mask.png \
  --pixels-per-unit 2 --unit css-px \
  --container 0 0 160 80 --out /path/to/new-diagnostics
```

--container is the reference rectangle in **image pixels**, in left/top/right/bottom order; right and bottom are exclusive. It defaults to the entire crop. Use it as a comparison frame, not proof that its center is the intended target. Native screenshots can use --unit pt with a measured pixels-per-point ratio.

When a screenshot or recording has no reliable scale, use --unit image-px --pixels-per-unit 1. Report only image-pixel diagnostics; obtain calibrated live rendering before proposing CSS/point offsets.

The script writes the unchanged source, foreground mask, two padded mask blurs, two whole-scene blurs, a guided view, a comparison sheet, and measurements.json. Whole-scene blurs include the container and neighboring content; they do not simulate blurring only the mark. Capture enough surrounding space to judge that relationship. Inspect the mask before trusting numbers. Measurements include visible bounds, weighted centroid, rectangular edge gaps, and reference-center displacement in the declared units. Pixel centers are measured at x+0.5, y+0.5. Negative gaps mean overflow; zero is not substituted.

Limits that change interpretation:

- The 16/255 visibility threshold suppresses faint pixels; it is not a perceptual boundary. Very faint marks may be rejected. Background mode uses approximate sRGB luminance difference, not a model of human vision; use an isolated coverage mask for problematic colors.
- Gaps are to the reference **rectangle**, not to its rounded contour. Judge curved-endcap whitespace from the contextual clear/blurred views; do not claim the script measures curved negative space or text baselines.
- Blur is based on the mark's size and padded to avoid truncating its spread. Symmetric normalized blur does not move the full linear centroid; the blurred blob is a diagnostic view, not a better automatic center.
- Alpha-only previews are composited on gray for visibility. Inspect the mark on its real background before choosing a correction. Diagnostic guides and blur never ship in product UI.

## Compare a small set of corrections

Use the suspected direction and the named relationship to choose candidates, including the unchanged original. A half-unit and one-unit move are useful initial probes, not fixed rules or acceptance thresholds. Apply candidates temporarily to the real component and capture each under identical conditions; do not move an entire screenshot or paint over the old mark to simulate a correction.

Review original-size clear views first, then use blur to examine mass and surrounding whitespace. If there is no clear improvement, retain the original. If candidates disagree across sizes or content, revisit the asset, font, or alignment contract instead of accumulating offsets.

Implement a justified correction once in the shared inner mark. Preserve the outer control, hit target, focus ring, accessible label, clipping, and existing hover/pressed/animation transforms. Compose with existing transforms rather than replacing them. Avoid changing a whole icon family based on one glyph. Text-to-text relationships still follow baselines; do not vertically center every string by its ink bounds.

## Verify and report

Recheck the clean component at 100% scale in its actual context, relevant sizes, themes, and representative content (including localization/RTL when supported). Confirm container/track geometry and interaction areas remain stable. If only a screenshot is available, deliver diagnosis and candidates; do not claim source edits, live geometry, or interaction verification.

Report the visual relationship, structural baseline, foreground/scale assumptions, chosen correction and location (or why unchanged), before/after clear views, and relevant measurements. Separate geometric facts from visual judgments. Record the reason for an intentional optical offset near the shared implementation when it is otherwise non-obvious.

Run the script's focused checks after changing its measurement logic:

```bash
"$PYTHON" -m unittest discover -s /path/to/optical-align/tests -v
```

Keep execution bounded: reuse the environment/project supervisor for script and browser work with explicit time, memory, and process limits; on cancellation/failure clean up its exact process group. Input is limited to a single PNG, at most 1,048,576 pixels and 16 MiB per file. No browser daemon or repeated screenshot polling is needed for offline analysis.
