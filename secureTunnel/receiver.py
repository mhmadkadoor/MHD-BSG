import socket
import base64
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
try:
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import unpad
except ImportError:
    # Fallback if pycryptodome exposes Cryptodome namespace
    try:
        from Cryptodome.Cipher import AES
        from Cryptodome.Util.Padding import unpad
    except ImportError as e:
        raise SystemExit(
            "AES backend not found. Install one of:\n"
            "  - pycryptodome (provides 'Crypto' namespace)\n"
            "  - pycryptodomex (provides 'Cryptodome' namespace)\n\n"
            "Example:\n  py -m pip install pycryptodome"
        ) from e

HOST = '127.0.0.1'
PORT = 65433

def start_receiver():
    print(f"Receiver starting on {HOST}:{PORT}...")

    # Generate RSA key pair (2048-bit)
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((HOST, PORT))
            s.listen()
            print("Receiver waiting for connection...")
            while True:
                conn, addr = s.accept()
                with conn:
                    print(f"Receiver connected by {addr}")

                    # Send public key PEM to the client immediately
                    conn.sendall(public_pem)

                    buffer = b""
                    aes_key = None
                    while True:
                        data = conn.recv(4096)
                        if not data:
                            print(f"Connection closed by {addr}")
                            break
                        buffer += data

                        # Process complete lines (messages delimited by newline)
                        while b"\n" in buffer:
                            line, buffer = buffer.split(b"\n", 1)
                            if not line:
                                continue
                            # Handle AES key exchange and encrypted messages
                            if line.startswith(b"KEY:"):
                                try:
                                    enc_key_b64 = line[4:]
                                    enc_key = base64.b64decode(enc_key_b64)
                                    aes_key = private_key.decrypt(
                                        enc_key,
                                        padding.OAEP(
                                            mgf=padding.MGF1(algorithm=hashes.SHA256()),
                                            algorithm=hashes.SHA256(),
                                            label=None,
                                        ),
                                    )
                                    if len(aes_key) not in (16, 24, 32):
                                        print("Received AES key has invalid length.")
                                        aes_key = None
                                    else:
                                        print("Receiver: AES session key established.")
                                except Exception:
                                    print("Receiver: Failed to establish AES key.")
                                continue

                            if line.startswith(b"MSG:") and aes_key:
                                try:
                                    payload = base64.b64decode(line[4:])
                                    iv = payload[:16]
                                    ct = payload[16:]
                                    cipher = AES.new(aes_key, AES.MODE_CBC, iv)
                                    pt = unpad(cipher.decrypt(ct), 16)
                                    print(f"Receiver (AES) decrypted: {pt.decode('utf-8', errors='replace')}")
                                except Exception:
                                    print("Receiver: AES decryption failed.")
                                continue

                            # Fallback: try RSA direct message
                            try:
                                ciphertext = base64.b64decode(line)
                                plaintext = private_key.decrypt(
                                    ciphertext,
                                    padding.OAEP(
                                        mgf=padding.MGF1(algorithm=hashes.SHA256()),
                                        algorithm=hashes.SHA256(),
                                        label=None,
                                    ),
                                )
                                print(f"Receiver (RSA) decrypted: {plaintext.decode('utf-8', errors='replace')}")
                            except Exception:
                                # If not base64/encrypted, just show raw text
                                try:
                                    print(f"Receiver received (raw): {line.decode('utf-8', errors='replace')}")
                                except Exception:
                                    print("Receiver received non-text data.")
                    print("Receiver waiting for connection...")
    except KeyboardInterrupt:
        print("\nReceiver stopping...")

if __name__ == "__main__":
    start_receiver()
