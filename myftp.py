import socket
import os
import random
from getpass import getpass


class Client:
    def __init__(self):
        self.client_socket = None

    def is_connected(self):
        return self.client_socket is not None

    def disconnect(self):
        if self.is_connected():
            self.send_ftp("QUIT")
            self.client_socket.close()
            self.client_socket = None
            return
        print("Not connected.")

    def send_ftp(self, message):
        if not self.is_connected():
            print("Not connected.")
            return
        self.client_socket.sendall((message + "\r\n").encode())
        resp = self.client_socket.recv(1024).decode()
        print(resp, end="")

        if resp.startswith("550 Closing"):
            print("Connection closed by remote host.")
            self.client_socket.close()
            self.client_socket = None
        return resp

    def open_ftp(self, ip=None, port="21"):
        if self.is_connected():
            print(f"Already connected to {ip}, use disconnect first.")
            return

        if ip is None:
            user_input = input("To: ").split()
            if len(user_input) == 0 or len(user_input) > 2:
                print("Usage: open host name [port]")
                return
            ip = user_input[0]
            port = user_input[1] if len(user_input) == 2 else port
        try:
            if not port.isdigit():
                print(f"{ip}: bad port number\nUsage: open host name [port]")
                return
            self.client_socket = socket.socket(
                socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((ip, int(port)))
            resp = self.client_socket.recv(1024)

            if resp.decode().startswith("220"):
                print(f"Connected to {ip}.")
            print(resp.decode(), end="")
            self.send_ftp("OPTS UTF8 ON")
            self.authen(ip)
            return

        except socket.timeout:
            print(f"> ftp: connect :Connection timed out")
            return
        except Exception as e:
            print(e)
            return

    def authen(self, ip=None, user=None, password=None):
        if not self.is_connected():
            print("Not connected.")
            return

        if user is None:
            if ip:
                user = input(f"User ({ip}:(none)): ")
            else:
                user = input("Username: ")
            if not user:
                print("Login failed.")
                return
        resp = self.send_ftp(f"USER {user}")
        if resp.startswith("331"):
            if not password:
                password = getpass(f"Password: ")
            res = self.send_ftp(f"PASS {password}")
            if res.startswith("230"):
                return
        print("Login failed.")

    def ascii(self):
        return self.send_ftp("TYPE A")

    def binary(self):
        return self.send_ftp("TYPE I")

    def cd(self, path):
        if self.is_connected():
            if not path:
                path = input("Remote directory ")
        self.send_ftp(f'CWD {path}')

    def delete(self, remote_file=None):
        if self.is_connected():
            if not remote_file:
                remote_file = input("Remote file ")
            self.send_ftp(f"DELE {remote_file}")
        else:
            print("Not connected.")
    
    def mkdir(self, path):
        if self.is_connected():
            if not path:
                path = input("Remote directory ")
        self.send_ftp(f'MKD {path}')

    def pwd(self):
        return self.send_ftp("XPWD")

    def rename(self, old=None, new=None):
        self.send_ftp(f"RNTO {new}")

    def close(self, remote_file=None):
        if self.is_connected():
            if not remote_file:
                remote_file = input("Remote file ")
            self.send_ftp(f"DELE {remote_file}")
        else:
            print("Not connected.")

    def put(self, local_file=None, remote_file=None):
        if not self.is_connected():
            print("Not connected.")
            return
        if local_file is None:
            local_file = input("Local file ")
        if not os.path.exists(local_file):
            print(f"local: {local_file}: No such file or directory.")
            return
        if remote_file is None:
            remote_file = input("Remote file ")
        with open(local_file, "rb") as f:
            self.send_ftp(f"STOR {remote_file}")
            while True:
                data = f.read(1024)
                if not data:
                    break
                self.client_socket.sendall(data)
        print(f"local: {local_file} remote: {remote_file}")


client = Client()

while True:
    try:
        line = input("ftp> ").strip()
        args = line.split()

        if not line:
            continue

        if len(args) == 0:
            continue

        command = args[0]

        if command in ["quit", "bye"]:
            if client.is_connected():
                client.disconnect()
            break

        elif command in ["disconnect", "close"]:
            client.disconnect()

        elif command == "open":
            client.open_ftp(*args[1:])

        elif command == "ascii":
            client.ascii()

        elif command == "binary":
            client.binary()

        elif command == "cd":
            client.cd(args[1] if len(args) > 1 else None)

        elif command == "delete":
            client.delete(args[1] if len(args) > 1 else None)
        
        elif command == "ls":
            client.send_ftp("LIST")

        elif command == "put":
            client.put(args[1] if len(args) > 1 else None,
                       args[2] if len(args) > 2 else None)

        elif command == "pwd":
            client.pwd()

        elif command == "mkdir":
            client.mkdir(args[1] if len(args) > 1 else None)

        elif command == "lcd":
            if len(args) == 1:
                print(client.local_dir)
            else:
                client.local_dir = args[1]

        elif command == "rename":
            if len(args) > 2:
                client.rename(*args[1:])
            else:
                client.rename()

        elif command == "user":
            if len(args) > 1:
                client.authen(None, *args[1:])
            else:
                client.authen()

        elif command == "connected":
            print(client.is_connected())

        else:
            print("Invalid command.")

    except Exception as e:
        print(e)
        break
