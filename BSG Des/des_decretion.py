import des

def hex_to_str(hex_str):
    bytes_obj = bytes.fromhex(hex_str)
    return bytes_obj.decode("utf-8")

if __name__ == '__main__':
    print("--- DES Decryption ---")
    # Ciphertext from the previous encryption step
    cipher_input = input("Enter the Ciphertext (Hex): ")
    if not cipher_input:
        print("No ciphertext entered, using default demo value.")
        cipher_hex = "25ACC0739D080752"
    else:
        cipher_hex = cipher_input

    key_input = input("Enter the 16-char Hex Key (default: 133457799BBCDFF1): ")
    if not key_input:
        key = "133457799BBCDFF1"
    else:
        key = key_input
        if len(key) != 16:
             print("Warning: Key length is not 16 characters. Using default key.")
             key = "133457799BBCDFF1"
    
    print(f"Cipher Text (Hex): {cipher_hex}")
    print(f"Key (Hex): {key}")
    
    # Generate keys
    keys = des.generate_keys(key)
    
    # For decryption, we use the keys in reverse order
    keys_reversed = keys[::-1]
    
    # Decrypt
    # Note: The encrypt function in des.py implements the Feistel network.
    # DES decryption is the same algorithm as encryption but with reversed subkeys.
    decrypted_bin = des.encrypt(cipher_hex, keys_reversed)
    decrypted_hex = des.bin2hex(decrypted_bin)
    
    print(f"Decrypted Text (Hex): {decrypted_hex}")
    
    # Convert back to string
    try:
        decrypted_text = hex_to_str(decrypted_hex)
        print(f"Decrypted Text (String): '{decrypted_text}'")
    except Exception as e:
        print(f"Error converting to string: {e}")
