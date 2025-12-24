import socket

HOST = '127.0.0.1'
PORT = 65433

def start_receiver():
    print(f"Receiver starting on {HOST}:{PORT}...")
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((HOST, PORT))
            s.listen()
            s.settimeout(1.0)
            print("Receiver waiting for connection...")
            while True:
                try:
                    conn, addr = s.accept()
                except socket.timeout:
                    continue

                with conn:
                    print(f"Receiver connected by {addr}")
                    conn.settimeout(1.0)
                    while True:
                        try:
                            data = conn.recv(1024)
                        except socket.timeout:
                            continue

                        if not data:
                            print(f"Connection closed by {addr}")
                            break
                        print(f"Receiver received: {data.decode()}")
                    print("Receiver waiting for connection...")
    except KeyboardInterrupt:
        print("\nReceiver stopping...")

if __name__ == "__main__":
    start_receiver()
