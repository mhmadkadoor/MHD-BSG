import hashlib
import random
import base64

# lab2.py

def prng_keystream(seed: bytes):
    """Deterministic keystream from a seed (bytes)."""
    seed_int = int.from_bytes(seed, "big")
    rng = random.Random(seed_int)
    while True:
        yield rng.getrandbits(8)

def prng_xor_encrypt(seed: bytes, data: bytes) -> bytes:
    ks = prng_keystream(seed)
    return bytes(b ^ next(ks) for b in data)


key = b"123"
text = b"merhaba dunya! bu bir test mesajidir."

# Encrypt
ciphertext = prng_xor_encrypt(key, text)
print("cipher (base64):", base64.b64encode(ciphertext).decode())

recovered = prng_xor_encrypt(key, ciphertext)
print("recovered:", recovered.decode())