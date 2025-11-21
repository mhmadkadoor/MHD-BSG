"""
Decrypt an XOR-ciphered image using the key image (random_image.png).

Reads 'cyphered.png' and 'random_image.png' from the current folder,
applies XOR per pixel/channel, and writes 'decrptedimage.png'.
The operation is symmetric to encryption in 'lab3-2.py'. If sizes differ,
the key image is resized to match the ciphered image's size.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image


def _load_rgb_image(path: Path) -> Image.Image:
    img = Image.open(path)
    return img.convert("RGB")


def xor_decrypt_image(
    cipher_image_path: Path,
    key_image_path: Path,
    output_path: Path,
) -> Path:
    """XOR-decrypt ciphered image with key image and save output.

    Args:
        cipher_image_path: Path to 'cyphered.png'.
        key_image_path: Path to 'random_image.png'.
        output_path: Path to save decrypted image (e.g., 'decrptedimage.png').

    Returns:
        The output path after saving.
    """

    cipher_img = _load_rgb_image(cipher_image_path)
    key_img = _load_rgb_image(key_image_path)

    # Match lab3-2 behavior: resize key to base (cipher) image size if needed
    if cipher_img.size != key_img.size:
        key_img = key_img.resize(cipher_img.size, Image.NEAREST)

    cipher_arr = np.asarray(cipher_img, dtype=np.uint8)
    key_arr = np.asarray(key_img, dtype=np.uint8)

    # XOR again to recover the original
    plain_arr = np.bitwise_xor(cipher_arr, key_arr)

    plain_img = Image.fromarray(plain_arr)
    plain_img.save(output_path)
    print(f"Decrypted image saved to: {output_path}")
    return output_path


def _main(argv: list[str]) -> int:
    cwd = Path.cwd()
    cipher = cwd / "cyphered.png"
    key = cwd / "random_image.png"
    out = cwd / "decrptedimage.png"

    missing = [p.name for p in (cipher, key) if not p.exists()]
    if missing:
        print("Missing required file(s): " + ", ".join(missing))
        if "cyphered.png" in missing:
            print("- Create it by running 'lab3-2.py' first.")
        if "random_image.png" in missing:
            print("- Generate it by running 'lab3-1.py'.")
        print("No output was created.")
        return 0

    xor_decrypt_image(cipher, key, out)
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
