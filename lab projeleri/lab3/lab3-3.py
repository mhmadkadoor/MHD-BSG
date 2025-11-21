"""
Display comparison via RGB histograms: 'labtop.png' vs 'cyphered.png'.

This script loads both images, computes the histogram for each RGB channel,
and saves a side-by-side plot as 'hist_compare.png'. If sizes differ, it's
fine—histograms are independent of image dimensions. If files are missing,
the script explains how to generate them.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image
import matplotlib.pyplot as plt


def _load_rgb(path: Path) -> Image.Image:
    img = Image.open(path)
    return img.convert("RGB")


def _channel_hist(arr: np.ndarray, ch: int) -> np.ndarray:
    counts, _ = np.histogram(arr[..., ch], bins=256, range=(0, 256))
    return counts


def compare_images(img1_path: Path, img2_path: Path) -> None:
    img1 = _load_rgb(img1_path)
    img2 = _load_rgb(img2_path)

    a = np.asarray(img1, dtype=np.uint8)
    b = np.asarray(img2, dtype=np.uint8)

    colors = ["red", "green", "blue"]
    titles = ["Red", "Green", "Blue"]

    fig, axes = plt.subplots(nrows=3, ncols=2, figsize=(12, 8), sharex=True)
    fig.suptitle("RGB Histograms: labtop.png (left) vs decrptedimage.png (right)")

    for ch in range(3):
        left_ax = axes[ch, 0]
        right_ax = axes[ch, 1]

        h1 = _channel_hist(a, ch)
        h2 = _channel_hist(b, ch)
        ymax = max(h1.max(), h2.max())

        x = np.arange(256)
        left_ax.plot(x, h1, color=colors[ch])
        right_ax.plot(x, h2, color=colors[ch])
        left_ax.set_ylim(0, ymax * 1.05)
        right_ax.set_ylim(0, ymax * 1.05)
        left_ax.set_ylabel(titles[ch])

        if ch == 0:
            left_ax.set_title(img1_path.name)
            right_ax.set_title(img2_path.name)

    for ax in axes[-1, :]:
        ax.set_xlabel("Intensity (0-255)")

    plt.tight_layout(rect=(0, 0, 1, 0.95))
    out_path = Path.cwd() / "hist_compare2.png"
    fig.savefig(out_path)
    plt.close(fig)
    print(f"Histogram comparison saved to: {out_path}")


def main() -> int:
    cwd = Path.cwd()
    base = cwd / "labtop.png"
    comp = cwd / "decrptedimage.png"

    missing = [p.name for p in (base, comp) if not p.exists()]
    if missing:
        print("Missing required file(s): " + ", ".join(missing))
        if "labtop.png" in missing:
            print("- Place your original image as 'labtop.png' in this folder.")
        if "cyphered.png" in missing:
            print("- Create it by running 'lab3-2.py' (it uses 'random_image.png').")
        return 0

    compare_images(base, comp)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
