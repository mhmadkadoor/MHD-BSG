"""Quantize RGB channels + optional JPEG encoding, with metadata stripping.

Layer 1 (your idea):
- Remove the 'ones' digit per RGB channel to save bits, e.g. 255 -> 250, 25 -> 20.

Layer 2 (JPEG method):
- After quantization, optionally encode as JPEG (quality/subsampling/progressive).

Metadata:
- By default, strips EXIF/XMP/ICC and other metadata (shutter speed, ISO, timestamps, etc.).

Typical usage (from repo root):
    python image_comp/compress_image.py

Default:
- Reads:  image_comp/image.png
- Writes: image_comp/image_compressed.jpg

Dependency:
    pip install pillow
"""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageFilter


SCRIPT_DIR = Path(__file__).resolve().parent


def quantize_channel_value(v: int, step: int) -> int:
    # Round down to nearest multiple of `step`.
    # For step=10: 0..9 -> 0, 10..19 -> 10, ..., 255 -> 250
    return v - (v % step)


def strip_metadata(img: Image.Image) -> Image.Image:
    """Return a new image with the same pixels but without metadata.

    Pillow stores metadata in fields like img.info and format-specific chunks.
    Rebuilding from raw pixels drops EXIF/XMP/ICC and textual chunks.
    """
    # Ensure we materialize pixels and detach from original file/decoder state.
    rebuilt = Image.frombytes(img.mode, img.size, img.tobytes())
    return rebuilt


def _parse_rgb_background(value: str) -> tuple[int, int, int]:
    v = value.strip().lower()
    if v in {"white", "w"}:
        return (255, 255, 255)
    if v in {"black", "b"}:
        return (0, 0, 0)
    if v.startswith("#"):
        v = v[1:]
    if len(v) != 6 or any(c not in "0123456789abcdef" for c in v):
        raise ValueError("alpha background must be 'white', 'black', or a hex color like #ffffff")
    return (int(v[0:2], 16), int(v[2:4], 16), int(v[4:6], 16))


def _jpeg_subsampling_to_pillow(value: str) -> int:
    # Pillow uses: 0=4:4:4, 1=4:2:2, 2=4:2:0
    v = value.strip().lower().replace(":", "")
    if v in {"444", "44"}:
        return 0
    if v in {"422", "42"}:
        return 1
    if v in {"420", "40"}:
        return 2
    raise ValueError("jpeg-subsampling must be one of: 444, 422, 420")


def compress_image(
    input_path: Path,
    output_path: Path,
    step: int = 10,
    *,
    max_side: int | None = 1000,
    blur_radius: float = 0.6,
    strip_meta: bool = True,
    jpeg_quality: int = 75,
    jpeg_subsampling: str = "420",
    jpeg_progressive: bool = False,
    alpha_background: str = "white",
) -> None:
    if step <= 0 or step > 255:
        raise ValueError("step must be in the range 1..255")

    if jpeg_quality < 1 or jpeg_quality > 95:
        raise ValueError("jpeg_quality must be in the range 1..95")

    if max_side is not None and max_side <= 0:
        raise ValueError("max_side must be a positive integer")

    if blur_radius < 0:
        raise ValueError("blur_radius must be >= 0")

    with Image.open(input_path) as img:
        # Preserve alpha if present.
        if img.mode in {"RGBA", "LA"}:
            rgba = img.convert("RGBA")
            r, g, b, a = rgba.split()
            r = r.point(lambda v: quantize_channel_value(int(v), step))
            g = g.point(lambda v: quantize_channel_value(int(v), step))
            b = b.point(lambda v: quantize_channel_value(int(v), step))
            out = Image.merge("RGBA", (r, g, b, a))
        else:
            rgb = img.convert("RGB")
            r, g, b = rgb.split()
            r = r.point(lambda v: quantize_channel_value(int(v), step))
            g = g.point(lambda v: quantize_channel_value(int(v), step))
            b = b.point(lambda v: quantize_channel_value(int(v), step))
            out = Image.merge("RGB", (r, g, b))

        # Optional lossy pre-processing steps.
        # 1) Downscale (often the biggest size reduction).
        if max_side is not None:
            w, h = out.size
            if w > max_side or h > max_side:
                scale = max_side / float(max(w, h))
                new_size = (max(1, int(round(w * scale))), max(1, int(round(h * scale))))
                out = out.resize(new_size, resample=Image.Resampling.LANCZOS)

        # 2) Slight blur reduces high-frequency detail that costs bits in JPEG.
        if blur_radius > 0:
            out = out.filter(ImageFilter.GaussianBlur(radius=blur_radius))

        if strip_meta:
            out = strip_metadata(out)

        output_path.parent.mkdir(parents=True, exist_ok=True)

        suffix = output_path.suffix.lower()
        if suffix in {".jpg", ".jpeg"}:
            # JPEG does not support alpha; composite RGBA over a solid background.
            if out.mode == "RGBA":
                bg = _parse_rgb_background(alpha_background)
                background = Image.new("RGB", out.size, bg)
                background.paste(out, mask=out.split()[3])
                out_to_save = background
            else:
                out_to_save = out.convert("RGB")

            out_to_save.save(
                output_path,
                format="JPEG",
                quality=jpeg_quality,
                optimize=True,
                progressive=jpeg_progressive,
                subsampling=_jpeg_subsampling_to_pillow(jpeg_subsampling),
                # Do not carry over metadata.
                exif=b"",
            )
        else:
            # PNG typically benefits from reduced color variety.
            # optimize=True asks Pillow to spend more CPU to reduce file size.
            out.save(output_path, format="PNG", optimize=True)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Default (no args) runs a full combo: quantize + no-metadata + lossy resize/blur + JPEG. "
            "Use flags to override."
        )
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=SCRIPT_DIR / "image.png",
        help="Input image path (default: image_comp/image.png)",
    )
    parser.add_argument(
        "--combo",
        action="store_true",
        help=(
            "Apply the full combo pipeline with aggressive defaults: quantize + no-metadata + "
            "lossy resize/blur + JPEG (use this if your output is getting bigger)"
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=SCRIPT_DIR / "image_combo.jpg",
        help=(
            "Output image path. Use .jpg/.jpeg for JPEG compression, or .png for PNG "
            "(default: image_comp/image_combo.jpg)"
        ),
    )
    parser.add_argument(
        "--step",
        type=int,
        default=10,
        help="Quantization step. Use 10 to remove ones digit (default: 10)",
    )
    parser.add_argument(
        "--max-side",
        type=int,
        default=1000,
        help=(
            "Optional lossy resize: limit the longest side (width or height) to this many pixels "
            "(keeps aspect ratio). Example: --max-side 800"
        ),
    )
    parser.add_argument(
        "--blur-radius",
        type=float,
        default=0.6,
        help=(
            "Optional lossy Gaussian blur radius (pixels). Example: 0.3, 0.6, 1.0. "
            "Use small values to avoid obvious blur (default: 0.6)"
        ),
    )
    parser.add_argument(
        "--strip-metadata",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Strip EXIF/XMP/ICC and other metadata (default: enabled)",
    )
    parser.add_argument(
        "--jpeg-quality",
        type=int,
        default=45,
        help="JPEG quality (1-95). Only used when output is .jpg/.jpeg (default: 45)",
    )
    parser.add_argument(
        "--jpeg-subsampling",
        type=str,
        default="420",
        choices=["444", "422", "420"],
        help="JPEG chroma subsampling: 444, 422, 420 (default: 420)",
    )
    parser.add_argument(
        "--jpeg-progressive",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Enable/disable progressive JPEG. Only for .jpg/.jpeg (default: disabled)",
    )
    parser.add_argument(
        "--alpha-background",
        type=str,
        default="white",
        help=(
            "When input has transparency and output is JPEG, composite over this background: "
            "'white', 'black', or a hex color like #ffffff (default: white)"
        ),
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    # Normalize paths for consistent behavior regardless of current working directory.
    args.input = Path(args.input)
    args.output = Path(args.output)

    if not args.input.exists():
        raise SystemExit(f"Input not found: {args.input}")

    # Combo mode: force a practical, smaller-output set of defaults.
    # (Defaults are already set to the combo pipeline; this keeps the flag meaningful.)
    if args.combo:
        if args.output.suffix.lower() not in {".jpg", ".jpeg"}:
            args.output = args.output.with_suffix(".jpg")

        # Aggressive defaults aimed at file size.
        args.strip_metadata = True
        args.step = 10
        args.max_side = 1000
        args.blur_radius = 0.6
        args.jpeg_quality = 45
        args.jpeg_subsampling = "420"
        args.jpeg_progressive = False

    compress_image(
        args.input,
        args.output,
        step=args.step,
        max_side=args.max_side,
        blur_radius=args.blur_radius,
        strip_meta=args.strip_metadata,
        jpeg_quality=args.jpeg_quality,
        jpeg_subsampling=args.jpeg_subsampling,
        jpeg_progressive=args.jpeg_progressive,
        alpha_background=args.alpha_background,
    )
    print(f"Wrote: {args.output}")


if __name__ == "__main__":
    main()
