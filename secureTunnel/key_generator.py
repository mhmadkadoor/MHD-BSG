import datetime
from typing import Optional


# Symmetric crypto sizes (for this project)
# AES uses a 16-byte block size; common AES keys are 16/24/32 bytes.
AES_KEY_SIZE_BYTES = 16
AES_IV_SIZE_BYTES = 16


def _default_seed() -> int:
    # Keep the same *methodology* as the original script: seed from time.
    # We use microsecond and a small constant offset like the original.
    return int(datetime.datetime.now().microsecond)


def generate_key(value: int) -> int:
    """Generate a (variable-length) key integer using Collatz parity.

    This keeps the original methodology:
    - Start from a time-derived integer (or caller-provided value)
    - Iterate the Collatz transform
    - Shift the key and append a bit based on odd/even
      * odd  -> append 0
      * even -> append 1
    """
    value = int(value - 5)
    if value <= 1:
        value = 2
    key = 0
    while value > 1:
        key <<= 1
        if value & 1:
            value = int((value * 3) + 1)
        else:
            key |= 1
            value = int(value / 2)
    return key


def generate_key_bytes(n_bytes: int, seed: Optional[int] = None) -> bytes:
    """Generate exactly `n_bytes` using Collatz-parity bits.

    The original `generate_key` stops once the Collatz sequence reaches 1,
    which gives a variable number of bits. For symmetric crypto we often need
    a fixed size.

    In the AES version of this project:
    - AES session key: 16 bytes (AES-128)  -> `generate_key_bytes(16)`
    - AES-CBC IV:      16 bytes (block)    -> `generate_key_bytes(16)`

    To preserve the same Collatz-parity methodology while producing enough
    bits, we restart the Collatz process with a derived value when the
    sequence terminates.
    """
    if n_bytes <= 0:
        raise ValueError("n_bytes must be positive")

    bits_needed = n_bytes * 8
    seed_value = _default_seed() if seed is None else int(seed)
    value = int(seed_value - 5)
    if value <= 1:
        value = 2

    out = 0
    bits_out = 0

    while bits_out < bits_needed:
        # If the Collatz sequence terminated, restart from a derived value.
        if value <= 1:
            # Derive a new value using the bits we already produced.
            # Still Collatz-based: the next bits are produced by Collatz parity.
            value = ((seed_value ^ (out & 0xFFFFFFFF)) + 2) | 1

        out <<= 1
        if value & 1:
            # odd -> append 0
            value = int((value * 3) + 1)
        else:
            # even -> append 1
            out |= 1
            value = int(value / 2)

        bits_out += 1

    return out.to_bytes(n_bytes, byteorder="big", signed=False)


def generate_aes_key(seed: Optional[int] = None) -> bytes:
    """Convenience wrapper for AES-128 session key (16 bytes)."""
    return generate_key_bytes(AES_KEY_SIZE_BYTES, seed=seed)


def generate_aes_iv(seed: Optional[int] = None) -> bytes:
    """Convenience wrapper for AES-CBC IV (16 bytes)."""
    return generate_key_bytes(AES_IV_SIZE_BYTES, seed=seed)


if __name__ == "__main__":
    kegenvalue = _default_seed()
    print(f"Key generation value: {kegenvalue}")
    generated_key = generate_key(kegenvalue)
    print(bin(generated_key))

    aes_key = generate_aes_key()
    aes_iv = generate_aes_iv()
    print(f"AES key (len={len(aes_key)}): {aes_key.hex()}")
    print(f"AES iv  (len={len(aes_iv)}): {aes_iv.hex()}")