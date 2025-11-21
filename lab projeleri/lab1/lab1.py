
def xor_str(a, b):
    result = ''
    for x, y in zip(a, b):
        result += chr(ord(x) ^ ord(y))
    return result


# def xor_str(a, b):
#     result = []
#     for x, y in zip(a, b):
#         xor_val = ord(x) ^ ord(y)
#         result.append(bin(xor_val)[2:].zfill(8))
#     return result

def block_encrypt(text, key, block_size=4):
    cipher = ""
    for i in range(0, len(text), block_size):
        block = text[i:i + block_size] 

        while len(block) < block_size:
            block += "-"

        for j in range(block_size):
            cipher += chr(ord(block[j]) ^ ord(key[j % len(key)]))
    
    return cipher


text = "MERHABAMERHABA"
text2 = "AAAAAAAAABBBBBBBB"
key = "KEY112312312"

encrypted = block_encrypt(text, key)
encrypted2 = block_encrypt(text2, key)

print("Şifreli:", [ord(c) for c in encrypted])
print("Şifreli2:", [ord(c) for c in encrypted2])

print("XOR Sonucu:", [ord(c) for c in xor_str(encrypted, encrypted2)])
print("XOR Sonucu:", [ord(c) for c in xor_str(text, text2)])