import socket
import os
from urllib.parse import urlparse

def find_free_port(start_port):
    port = int(start_port)
    while port < 65535:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('', port))
                return port
            except OSError:
                port += 1
    return -1

if __name__ == "__main__":
    req_flask = os.environ.get('FLASK_PORT', '5000')
    req_ws = 8765

    free_flask = find_free_port(req_flask)
    ws_start = req_ws
    if free_flask == ws_start:
        ws_start += 1
    free_ws = find_free_port(ws_start)
    while free_ws == free_flask:
        free_ws = find_free_port(free_ws + 1)

    # Host Server Logic
    input_url = os.environ.get('INPUT_URL', 'http://127.0.0.1:5000')
    try:
        p = urlparse(input_url)
        scheme = p.scheme or 'http'
        hostname = p.hostname or '127.0.0.1'
        final_host_server = f"{scheme}://{hostname}:{free_flask}"
    except:
        final_host_server = f"http://127.0.0.1:{free_flask}"

    print(f"{free_flask},{free_ws},{final_host_server}")