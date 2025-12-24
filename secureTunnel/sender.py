import socket
import base64
import os
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
try:
    from Crypto.Cipher import DES
    from Crypto.Util.Padding import pad
except ImportError:
    try:
        from Cryptodome.Cipher import DES
        from Cryptodome.Util.Padding import pad
    except ImportError as e:
        raise SystemExit(
            "DES backend not found. Install one of:\n"
            "  - pycryptodome (provides 'Crypto' namespace)\n"
            "  - pycryptodomex (provides 'Cryptodome' namespace)\n\n"
            "Example:\n  py -m pip install pycryptodome"
        ) from e

HOST = '127.0.0.1'
PORT = 65432 # Connects to the Tunnel

def start_sender():
    print(f"Sender connecting to {HOST}:{PORT}...")
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))

            # Receive receiver's public key PEM first
            buffer = b""
            end_marker = b"-----END PUBLIC KEY-----"
            while end_marker not in buffer:
                chunk = s.recv(4096)
                if not chunk:
                    raise ConnectionError("Disconnected before receiving public key")
                buffer += chunk
            pem_end_index = buffer.index(end_marker) + len(end_marker)
            public_pem = buffer[:pem_end_index]
            print("Received receiver public key.")

            public_key = serialization.load_pem_public_key(public_pem)

            # Generate a DES session key (8 bytes) and send it encrypted via RSA
            des_key = os.urandom(8)
            enc_key = public_key.encrypt(
                des_key,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None,
                ),
            )
            s.sendall(b"KEY:" + base64.b64encode(enc_key) + b"\n")
            print("Sent DES session key (RSA-encrypted).")

            print("Connected. Type messages to encrypt (Ctrl+C to quit):")
            while True:
                message = input("You: ")
                if not message:
                    continue
                iv = os.urandom(8)
                cipher = DES.new(des_key, DES.MODE_CBC, iv)
                ct = cipher.encrypt(pad(message.encode('utf-8'), 8))
                payload = iv + ct
                s.sendall(b"MSG:" + base64.b64encode(payload) + b"\n")
    except ConnectionRefusedError:
        print("Error: Could not connect to tunnel. Is unsecureTunnel.py running?")
    except KeyboardInterrupt:
        print("\nSender stopping...")

if __name__ == "__main__":
    start_sender()
