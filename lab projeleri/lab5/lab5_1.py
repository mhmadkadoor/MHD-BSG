IMG_PATH = "lab5/laptop.png"

import hashlib, numpy as np
from PIL import Image

img = Image.open(IMG_PATH).convert("RGB")
arr = np.array(img)
hash_value = hashlib.sha256(arr.tobytes()).hexdigest()
print("SHA-256:", hash_value)


from pathlib import Path
Path("orjinal_hash.txt").write_text(hash_value)
print("Hash value saved to orjinal_hash.txt")


stored_hash = Path("orjinal_hash.txt").read_text().strip()
new_hash = hashlib.sha256(np.array(Image.open(IMG_PATH).convert("RGB")).tobytes()).hexdigest()

if stored_hash == new_hash:
    print("The image is unchanged.")
else:
    print("The image has been modified.")


arr[0,0,0] = np.uint8((int(arr[0,0,0]) + 1) % 256)
img = Image.fromarray(arr).save("modified_image.png")
mod_hash = hashlib.sha256(np.array(Image.open("modified_image.png").convert("RGB")).tobytes()).hexdigest()

if mod_hash == stored_hash:
    print("The modified image is unchanged.")
else:
    print("The modified image has been altered.")


Path("mod_hash.txt").write_text(mod_hash)
print("Hash value saved to mod_hash.txt")