import socket
import time

HOST = '127.0.0.1'
PORT = 65432 # Connects to the Tunnel

def start_sender():
    print(f"Sender connecting to {HOST}:{PORT}...")
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))
            print("Connected to tunnel. Type your messages (Ctrl+C to quit):")
            while True:
                message = input("You: ")
                if message:
                    s.sendall(message.encode())
    except ConnectionRefusedError:
        print("Error: Could not connect to tunnel. Is unsecureTunnel.py running?")
    except KeyboardInterrupt:
        print("\nSender stopping...")

if __name__ == "__main__":
    start_sender()
