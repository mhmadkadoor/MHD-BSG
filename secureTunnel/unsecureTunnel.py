import socket
import threading

# Tunnel listens for Sender
LISTEN_HOST = '127.0.0.1'
LISTEN_PORT = 65432 

# Tunnel forwards to Receiver
TARGET_HOST = '127.0.0.1'
TARGET_PORT = 65433 

def start_tunnel():
    print(f"UnsecureTunnel starting on {LISTEN_HOST}:{LISTEN_PORT}...")

    def pipe(src, dst, direction):
        """Forward bytes from src to dst while logging."""
        try:
            while True:
                data = src.recv(4096)
                if not data:
                    print(f"{direction} disconnected.")
                    break
                try:
                    printable = data.decode('utf-8', errors='replace').strip()
                except Exception:
                    printable = str(data)
                print(f"Tunnel intercepted ({direction} ->): {printable}")
                dst.sendall(data)
        except Exception as e:
            pass

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind((LISTEN_HOST, LISTEN_PORT))
            server_socket.listen()
            print("Tunnel waiting for sender...")
            while True:
                sender_conn, sender_addr = server_socket.accept()
                print(f"Tunnel connected to sender: {sender_addr}")

                # Connect to receiver for this sender session
                client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                try:
                    print(f"Tunnel connecting to receiver at {TARGET_HOST}:{TARGET_PORT}...")
                    client_socket.connect((TARGET_HOST, TARGET_PORT))
                    print("Tunnel connected to receiver.")

                    # Start bidirectional forwarding
                    t1 = threading.Thread(target=pipe, args=(sender_conn, client_socket, 'sender'), daemon=True)
                    t2 = threading.Thread(target=pipe, args=(client_socket, sender_conn, 'receiver'), daemon=True)
                    t1.start()
                    t2.start()

                    # Wait until either side disconnects
                    while t1.is_alive() and t2.is_alive():
                        pass
                except ConnectionRefusedError:
                    print("Error: Could not connect to receiver. Is receiver.py running?")
                finally:
                    try:
                        client_socket.close()
                    except Exception:
                        pass
                    try:
                        sender_conn.close()
                    except Exception:
                        pass
                print("Tunnel waiting for sender...")
    except KeyboardInterrupt:
        print("\nTunnel stopping...")

if __name__ == "__main__":
    start_tunnel()
