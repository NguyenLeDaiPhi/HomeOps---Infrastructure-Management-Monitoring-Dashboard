import socket 
import json
import struct

LISTENER_IP = "192.168.2.1"
PORT = 5003

def recv_exact(sock, size):
    data = b''

    while len(data) < size: 
        chunk = sock.recv(size - len(data))

        if not chunk:
            return None
        
        data += chunk
    
    return data

def handle_payload(payload, addr):
    message_type = payload.get("type")
    hostname = payload.get("hostname")
    timestamp = payload.get("timestamp")

    print("\n==========================================")
    print(f"Host      : {hostname}")
    print(f"Time      : {timestamp}")
    print(f"Type      : {message_type}")
    print("==========================================")

    #
    # INITIAL SNAPSHOT
    #

    if message_type == "HARDWARE_METRICS": 
        print("\nCPU")
        print(json.dumps(payload["cpu"], indent=4))

        print("\nRAM")
        print(json.dumps(payload["ram"], indent=4))

        print("\nDISK")
        print(json.dumps(payload["disk"], indent=4))

    elif message_type == "INITIAL_SNAPSHOT":
        print("\nNETWORK")
        print(json.dumps(payload["network"], indent=4))

    # 
    # NETWORK UPDATE 
    #

    elif message_type == "NETWORK_EVENT":
        print("\nNETWORK EVENTS")
        print(json.dumps(payload["events"], indent=4))

        print("\nUPDATED NETWORK SNAPSHOT")
        print(json.dumps(payload["network"], indent=4))

    else:
        print("Unknow message type.")
    
def start_receiver():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((LISTENER_IP, PORT))
    server.listen(5)
    print(f"Listening on {LISTENER_IP}:{PORT}")

    try:
        client, addr = server.accept()
        while True:
            print(f"\nConnected: {addr[0]}:{addr[1]}")

            buffer = ""

            try:
                while True:
                    
                    header = recv_exact(client, 4)
                    if not header: 
                        print(f"{addr[0]} disconnected.") 
                        break

                    message_length = struct.unpack("!I", header)[0]

                    json_bytes = recv_exact(client, message_length)
                    if not json_bytes: 
                        print(f"{addr[0]} disconnected.")
                        break

                    payload = json.loads(json_bytes.decode('utf-8'))

                    handle_payload(payload, addr)

                    while "\n" in buffer: 
                        message, buffer = buffer.split("\n", 1)

                        if not message.strip():
                            continue

                        payload = json.loads(message)

                        handle_payload(payload, addr)
            except json.JSONDecodeError as e:
                print("Invalid JSON:", e)
            except ConnectionResetError:
                print(f"{addr[0]} disconnected unexpectedly.")
            finally: 
                client.close()
        
    except KeyboardInterrupt:
        print("\nReceiver stopped.")
    finally:
        server.close()

if __name__ == "__main__":
    start_receiver()

