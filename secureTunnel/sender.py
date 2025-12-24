import socket
import base64
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding

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

            print("Connected. Type messages to encrypt (Ctrl+C to quit):")
            while True:
                message = input("You: ")
                if not message:
                    continue
                ciphertext = public_key.encrypt(
                    message.encode('utf-8'),
                    padding.OAEP(
                        mgf=padding.MGF1(algorithm=hashes.SHA256()),
                        algorithm=hashes.SHA256(),
                        label=None,
                    ),
                )
                b64 = base64.b64encode(ciphertext) + b"\n"
                s.sendall(b64)
    except ConnectionRefusedError:
        print("Error: Could not connect to tunnel. Is unsecureTunnel.py running?")
    except KeyboardInterrupt:
        print("\nSender stopping...")

if __name__ == "__main__":
    start_sender()
