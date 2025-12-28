"""Quantize RGB channels + optional JPEG encoding.

Layer 1 (your idea):
- Remove the 'ones' digit per RGB channel to save bits, e.g. 255 -> 250, 25 -> 20.

Layer 2 (JPEG method):
- After quantization, optionally encode as JPEG (quality/subsampling/progressive).

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

from PIL import Image


def quantize_channel_value(v: int, step: int) -> int:
    # Round down to nearest multiple of `step`.
    # For step=10: 0..9 -> 0, 10..19 -> 10, ..., 255 -> 250
    return v - (v % step)


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
    jpeg_quality: int = 75,
    jpeg_subsampling: str = "420",
    jpeg_progressive: bool = True,
    alpha_background: str = "white",
) -> None:
    if step <= 0 or step > 255:
        raise ValueError("step must be in the range 1..255")

    if jpeg_quality < 1 or jpeg_quality > 95:
        raise ValueError("jpeg_quality must be in the range 1..95")

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
            )
        else:
            # PNG typically benefits from reduced color variety.
            # optimize=True asks Pillow to spend more CPU to reduce file size.
            out.save(output_path, format="PNG", optimize=True)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Compress-like quantization: remove ones digit of RGB channels "
            "(e.g., 255->250) and save as PNG."
        )
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("image_comp") / "image.png",
        help="Input image path (default: image_comp/image.png)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("image_comp") / "image_compressed.jpg",
        help=(
            "Output image path. Use .jpg/.jpeg for JPEG compression, or .png for PNG "
            "(default: image_comp/image_compressed.jpg)"
        ),
    )
    parser.add_argument(
        "--step",
        type=int,
        default=10,
        help="Quantization step. Use 10 to remove ones digit (default: 10)",
    )
    parser.add_argument(
        "--jpeg-quality",
        type=int,
        default=75,
        help="JPEG quality (1-95). Only used when output is .jpg/.jpeg (default: 75)",
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
        default=True,
        help="Enable/disable progressive JPEG. Only for .jpg/.jpeg (default: enabled)",
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
    if not args.input.exists():
        raise SystemExit(f"Input not found: {args.input}")

    compress_image(
        args.input,
        args.output,
        step=args.step,
        jpeg_quality=args.jpeg_quality,
        jpeg_subsampling=args.jpeg_subsampling,
        jpeg_progressive=args.jpeg_progressive,
        alpha_background=args.alpha_background,
    )
    print(f"Wrote: {args.output}")


if __name__ == "__main__":
    main()
