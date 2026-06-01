"""Remove the bright-blue mouse cursor decoration from each course tile image.

The cursors are baked into the source PNGs by the previous WordPress site.
This script identifies the saturated-blue cursor pixels via an HSV mask,
dilates the mask slightly to catch the cursor outline, then replaces those
pixels by sampling from a blurred copy of the image (a poor man's inpaint).
"""

from pathlib import Path

from PIL import Image, ImageFilter


COURSES_DIR = Path(__file__).resolve().parent.parent / "assets" / "images" / "courses"
OUTPUT_SUFFIX = "-clean"

# Cursor color range in HSV (Pillow uses 0-255 for all H/S/V channels).
# The cursor is a saturated bright blue, roughly #3a7eff – #5da0ff range.
HUE_MIN, HUE_MAX = 140, 175     # Blue hues in PIL's 0-255 scale (~205-247° / 1.41)
SAT_MIN = 130                    # Highly saturated
VAL_MIN = 130                    # Bright

# Dilation iterations on the mask so the cursor outline + anti-aliasing get
# caught, not just the solid fill.
DILATE_ITERATIONS = 3


def build_cursor_mask(img: Image.Image) -> Image.Image:
    hsv = img.convert("HSV")
    h, s, v = hsv.split()
    mask = Image.new("L", img.size, 0)
    h_data = h.load()
    s_data = s.load()
    v_data = v.load()
    m_data = mask.load()
    width, height = img.size
    for y in range(height):
        for x in range(width):
            if HUE_MIN <= h_data[x, y] <= HUE_MAX and s_data[x, y] >= SAT_MIN and v_data[x, y] >= VAL_MIN:
                m_data[x, y] = 255
    return mask


def dilate(mask: Image.Image, iterations: int = 1) -> Image.Image:
    out = mask
    for _ in range(iterations):
        out = out.filter(ImageFilter.MaxFilter(3))
    return out


def fill_masked_pixels(img: Image.Image, mask: Image.Image) -> Image.Image:
    """Replace masked pixels with surrounding content via a heavy blur of the
    UNMASKED image, used as the fill source.
    """
    # Heavily blur the original — this gives us a per-pixel "what color would
    # this area be without the cursor?" estimate from neighboring pixels.
    blurred = img.filter(ImageFilter.GaussianBlur(radius=14))
    # Composite: keep original where mask is black, take blurred where white.
    return Image.composite(blurred, img, mask)


def clean_image(src: Path, dst: Path) -> tuple[int, int]:
    img = Image.open(src).convert("RGB")
    mask = build_cursor_mask(img)
    mask = dilate(mask, DILATE_ITERATIONS)
    cleaned = fill_masked_pixels(img, mask)
    cleaned.save(dst, optimize=True)
    masked_pixels = sum(1 for px in mask.getdata() if px > 0)
    return masked_pixels, img.size[0] * img.size[1]


def main() -> None:
    targets = sorted(p for p in COURSES_DIR.glob("AIL-*.png") if "-clean" not in p.stem)
    if not targets:
        print(f"No course images found in {COURSES_DIR}")
        return
    for path in targets:
        dst = path.with_stem(path.stem + OUTPUT_SUFFIX)
        masked, total = clean_image(path, dst)
        pct = 100 * masked / total
        print(f"{path.name} -> {dst.name}  ({masked} cursor px, {pct:.2f}% of image)")


if __name__ == "__main__":
    main()
