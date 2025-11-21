from pathlib import Path
import numpy as np
from PIL import Image

# --- Yardımcı Fonksiyonlar (encoding ile uyumlu stil) ---

def _bytes_to_bits(b: bytes) -> np.ndarray:
	return np.unpackbits(np.frombuffer(b, dtype=np.uint8))


def _u32_to_bits(n: int) -> np.ndarray:
	return _bytes_to_bits(n.to_bytes(4, byteorder="big"))


def _bits_to_bytes(bits: np.ndarray) -> bytes:
	bits = np.asarray(bits, dtype=np.uint8).ravel()
	if bits.size % 8 != 0:
		raise ValueError("Bit sayısı 8'in katı olmalı")
	return np.packbits(bits).tobytes()


def _bits_to_u32(bits32: np.ndarray) -> int:
	bits32 = np.asarray(bits32, dtype=np.uint8).ravel()
	if bits32.size != 32:
		raise ValueError("Başlık 32 bit olmalı")
	return int.from_bytes(np.packbits(bits32).tobytes(), byteorder="big")


# --- Çözme (Decode) Fonksiyonu ---

def reveal_message_lsb(
	encoded_image_path: str,
	*,
	channel: str = "R",
	start_xy: tuple[int, int] = (0, 0),
) -> str:
	ch_index = {"R": 0, "G": 1, "B": 2}[channel.upper()]
	img = Image.open(encoded_image_path).convert("RGB")
	arr = np.array(img, dtype=np.uint8)
	H, W, _ = arr.shape

	sx, sy = start_xy
	if not (0 <= sx < W and 0 <= sy < H):
		raise ValueError("start_xy görüntü sınırları dışında.")

	flat = arr[:, :, ch_index].ravel()
	start = sy * W + sx
	lsb = (flat[start:] & 1).astype(np.uint8)

	
	length_bytes = _bits_to_u32(lsb[:32])
	total_bits = length_bytes * 8
	if 32 + total_bits > lsb.size:
		raise ValueError("Görselde yeterli bit yok")

	msg_bits = lsb[32 : 32 + total_bits]
	msg = _bits_to_bytes(msg_bits).decode("utf-8")
	return msg



here = Path(__file__).resolve().parent
encoded = str(here / "Hms.png")
out_txt = here / "Hms.txt"

message = reveal_message_lsb(encoded, channel="R", start_xy=(0, 0))
out_txt.write_text(message, encoding="utf-8")
print(message)




