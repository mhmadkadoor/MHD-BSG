import socket

# Tunnel listens for Sender
LISTEN_HOST = '127.0.0.1'
LISTEN_PORT = 65432 

# Tunnel forwards to Receiver
TARGET_HOST = '127.0.0.1'
TARGET_PORT = 65433 

def start_tunnel():
    print(f"UnsecureTunnel starting on {LISTEN_HOST}:{LISTEN_PORT}...")
    
    try:
        # Create socket to listen for sender
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.bind((LISTEN_HOST, LISTEN_PORT))
            server_socket.listen()
            server_socket.settimeout(1.0)
            
            print("Tunnel waiting for sender...")
            while True:
                try:
                    sender_conn, sender_addr = server_socket.accept()
                except socket.timeout:
                    continue
                
                with sender_conn:
                    print(f"Tunnel connected to sender: {sender_addr}")
                    sender_conn.settimeout(1.0)
                    
                    # Create socket to connect to receiver
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
                        try:
                            print(f"Tunnel connecting to receiver at {TARGET_HOST}:{TARGET_PORT}...")
                            client_socket.connect((TARGET_HOST, TARGET_PORT))
                            print("Tunnel connected to receiver.")
                            
                            while True:
                                try:
                                    data = sender_conn.recv(1024)
                                except socket.timeout:
                                    continue

                                if not data:
                                    print("Sender disconnected.")
                                    break
                                
                                message = data.decode()
                                print(f"Tunnel intercepted: {message}")
                                
                                # Forward to receiver
                                client_socket.sendall(data)
                                
                        except ConnectionRefusedError:
                            print("Error: Could not connect to receiver. Is receiver.py running?")
                        except ConnectionResetError:
                            print("Connection reset.")
                
                print("Tunnel waiting for sender...")
                            
    except KeyboardInterrupt:
        print("\nTunnel stopping...")

if __name__ == "__main__":
    start_tunnel()
