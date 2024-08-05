import argparse
import gzip
import os
import re
import socket
from threading import Thread


def main():
    print("Starting server...")
    parser = argparse.ArgumentParser("http server")
    parser.add_argument('-d', '--directory', help='specify a directory for the server to read files from')
    args = parser.parse_args()

    files = []
    for fname in os.listdir(args.directory):
        files.append(fname)

    server_socket = socket.create_server(("localhost", 4221), reuse_port=True)
    while True:
        sock, _ = server_socket.accept() # wait for client
        Thread(target=handle_socket, args=[sock, args.directory, files]).start()

def handle_socket(sock, dir_path, files):
        while True:
            data = sock.recv(1024)
            if not data:
                break
            data = data.decode('utf-8')
            split_data = data.split()
            if split_data[0] == 'POST':
                split_new = data.split('\n')
                file_name = split_data[1].split("/")[2]
                path = os.path.join(dir_path, file_name)
                with open(path, 'w') as fid:
                    fid.write(split_new[-1])
                sock.sendall(b"HTTP/1.1 201 Created\r\nContent-Length: 0\r\n\r\n")
            elif split_data[1] == '/':
                sock.sendall(b"HTTP/1.1 200 OK\r\nContent-Length: 0\r\n\r\n")
            elif split_data[1].startswith('/echo/'):
                echo_str = split_data[1].split("/")[2]
                echo_bytes = echo_str.encode()
                mtch = re.search('Accept-Encoding: (.*)\\r', data)
                enc_header = ""
                if mtch != None:
                    encoding = mtch.group(1)
                    encs = list(map(str.strip, encoding.split(',')))
                    if 'gzip' in encs:
                        enc_header = "Content-Encoding: gzip\r\n"
                        echo_bytes = gzip.compress(echo_bytes)
                sock.sendall(f"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n{enc_header}Content-Length: {len(echo_bytes)}\r\n\r\n".encode() + echo_bytes)
            elif split_data[1] == '/user-agent':
                mtch = re.search('User-Agent: (.*)\\r', data)
                ua = mtch.group(1)
                sock.sendall(f"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: {len(ua)}\r\n\r\n{ua}".encode())
            elif split_data[1].startswith('/files/'):
                file_name = split_data[1].split("/")[2]
                if file_name in files:
                    path = os.path.join(dir_path, file_name)
                    with open(path, 'rb') as fid:
                        content = fid.read()
                        sock.sendall(f"HTTP/1.1 200 OK\r\nContent-Type: application/octet-stream\r\nContent-Length: {len(content)}\r\n\r\n".encode() + content)
                else:
                    sock.sendall(b"HTTP/1.1 404 Not Found\r\nContent-Length: 0\r\n\r\n")
            else:
                sock.sendall(b"HTTP/1.1 404 Not Found\r\nContent-Length: 0\r\n\r\n")


if __name__ == "__main__":
    main()
