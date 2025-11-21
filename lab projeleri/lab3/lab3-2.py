"""
Cipher an image using a random key image (one-time-pad style XOR).

Default behavior:
- Reads 'labtop.png' and 'random_image.png' from the current folder
- XORs them per pixel and channel
- Writes the result to 'cyphered.png'

If sizes differ, the key is resized to the base image size. If required
files are missing, the script prints clear next steps and exits cleanly.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image


def _load_rgb_image(path: Path) -> Image.Image:
    img = Image.open(path)
    return img.convert("RGB")


def xor_cipher_image(
    base_image_path: Path,
    key_image_path: Path,
    output_path: Path,
    *,
    resize_key: bool = True,
) -> Path:
    """XOR-cipher base image with key image and save output.

    Args:
        base_image_path: Path to the image to cipher (e.g., 'labtop.png').
        key_image_path: Path to the key image (e.g., 'random_image.png').
        output_path: Where to save the ciphered image (e.g., 'cyphered.png').
        resize_key: If True, resize key to base image size when mismatched.

    Returns:
        The output path after saving.
    """

    base_img = _load_rgb_image(base_image_path)
    key_img = _load_rgb_image(key_image_path)

    if base_img.size != key_img.size:
        if not resize_key:
            raise ValueError(
                f"Image sizes differ: base={base_img.size}, key={key_img.size}."
            )
        key_img = key_img.resize(base_img.size, Image.NEAREST)

    base_arr = np.asarray(base_img, dtype=np.uint8)
    key_arr = np.asarray(key_img, dtype=np.uint8)

    # XOR per channel
    cipher_arr = np.bitwise_xor(base_arr, key_arr)

    cipher_img = Image.fromarray(cipher_arr)
    cipher_img.save(output_path)
    print(f"Cyphered image saved to: {output_path}")
    return output_path


def _main(argv: list[str]) -> int:
    cwd = Path.cwd()
    base = cwd / "labtop.png"
    key = cwd / "random_image.png"
    out = cwd / "cyphered.png"

    missing = [p.name for p in (base, key) if not p.exists()]
    if missing:
        print("Missing required file(s): " + ", ".join(missing))
        if "labtop.png" in missing:
            print("- Place your source image as 'labtop.png' in this folder or pass a path.")
        if "random_image.png" in missing:
            print("- Generate it by running 'lab3-1.py' to create random_image.png.")
        print("No output was created.")
        return 0

    xor_cipher_image(base, key, out)
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
