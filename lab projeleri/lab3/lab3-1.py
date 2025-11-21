"""
Generate and save a random RGB image using a fixed seed.

Replicates the function shown in the screenshot: it sets the NumPy
random seed, creates a random uint8 array of shape (height, width, 3),
converts it to a PIL Image, saves it as 'random_image.png', prints a
confirmation, and returns both the Image and the underlying array.
"""

from __future__ import annotations

import numpy as np
from PIL import Image


def generate_random_image_with_seed(image_size: tuple[int, int], seed: int):
	"""Create a random image with a deterministic seed.

	Args:
		image_size: (width, height) in pixels.
		seed: Random seed to produce the same image for the same inputs.

	Returns:
		A tuple of (PIL.Image.Image, numpy.ndarray) where the ndarray has
		dtype uint8 and shape (height, width, 3).
	"""

	# Tohumu ayarlıyoruz (aynı seed -> aynı rastgele dizi)
	np.random.seed(seed)

	# Her pikselin R, G, B değeri 0-255 arasında rastgele seçiliyor
	random_image_array = np.random.randint(
		0,
		256,  # Değer aralığı (0-255)
		(image_size[1], image_size[0], 3),  # Boyut (yükseklik, genişlik, 3 renk kanalı)
		dtype=np.uint8,
	)

	# Numpy dizisini görüntüye çeviriyoruz
	random_image = Image.fromarray(random_image_array)

	# Rastgele görüntüyü kaydediyoruz
	random_image.save("random_image.png")
	print("Rastgele görüntü 'random_image.png' olarak kaydedildi.")

	return random_image, random_image_array


if __name__ == "__main__":
	# Example run: 320x240 image with a fixed seed
	img, arr = generate_random_image_with_seed((320, 240), seed=42)
	# Keep a tiny confirmation that includes shape and dtype
	print(f"Created image with array shape {arr.shape} and dtype {arr.dtype}.")

