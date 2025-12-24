def get_key(p): return [ord(c) for c in (p + "X"*8)[:8]]

def encrypt(text, key):
    k = get_key(key)
    text += " " * ((8 - len(text) % 8) % 8)
    return [v for i in range(0, len(text), 8) for v in [(x + kv) for x, kv in zip([(ord(c) + kv) for c, kv in zip(text[i:i+8], k)][::-1], k)]]

def decrypt(vals, key):
    k = get_key(key)
    return "".join("".join(chr(x - kv) for x, kv in zip([(v - kv) for v, kv in zip(vals[i:i+8], k)][::-1], k)) for i in range(0, len(vals), 8)).rstrip()

if __name__ == "__main__":
    p, t = "KODLARIM", "MERHABAA"
    print(f"Original: {t}\nPassword: {p}")
    enc = encrypt(t, p)
    print(f"Encrypted: {enc}")
    dec = decrypt(enc, p)
    print(f"Decrypted: {dec}\nMatch: {t == dec}")
    
    p2 = "JODLARIM"
    dec2 = decrypt(enc, p2)
    print(f"Wrong Pass ({p2}): {dec2}\nMatch: {dec2 == t}")
