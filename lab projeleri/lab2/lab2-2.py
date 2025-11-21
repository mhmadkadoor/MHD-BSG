from datetime import datetime

def xor_encrypt_decrypt(seed: bytes, data: bytes) -> bytes:
    out = bytearray()
    for i, b in enumerate(data):
        out.append(b ^ seed[i % len(seed)])
    return bytes(out)



now = datetime.now()
date_str = now.strftime("%Y-%m-%d %H:%M:%S.%S")
seed = date_str.encode("utf-8") 

message = b"Hello, this is a secret message."

print("Date (used as seed):", date_str)
print("seed (raw):", seed)

encrypted = xor_encrypt_decrypt(seed, message)
print("Encrypted:", encrypted.hex())

decrypted = xor_encrypt_decrypt(seed, encrypted)
print("Decrypted message:", decrypted)


