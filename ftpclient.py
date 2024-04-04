import socket
import os
import random
import time
from getpass import getpass


class Client:
    def __init__(self):
        self.client_socket = None
        self.local_dir = os.getcwd()

    def is_connected(self):
        return self.client_socket is not None

    def disconnect(self):
        if self.is_connected():
            self.send_command("QUIT")
            self.client_socket.close()
            self.client_socket = None
            return
        print("Not connected.")

    def send_command(self, message):
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
            user_input = input("To ").split()
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
            self.send_command("OPTS UTF8 ON")
            self.authen(ip)
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
        resp = self.send_command(f"USER {user}")
        if resp.startswith("331"):
            if not password:
                password = getpass(f"Password: ")
            res = self.send_command(f"PASS {password}")
            if res.startswith("230"):
                return
        print("Login failed.")

    def ascii(self):
        return self.send_command("TYPE A")

    def binary(self):
        return self.send_command("TYPE I")

    def cd(self, path):
        if self.is_connected():
            if not path:
                path = input("Remote directory ")
        self.send_command(f'CWD {path}')

    def delete(self, remote_file=None):
        if self.is_connected():
            if not remote_file:
                remote_file = input("Remote file ")
            self.send_command(f"DELE {remote_file}")
        else:
            print("Not connected.")

    def mkdir(self, path):
        if self.is_connected():
            if not path:
                path = input("Remote directory ")
        self.send_command(f'MKD {path}')

    def pwd(self):
        return self.send_command("XPWD")

    def rename(self, from_name=None, to_name=None):
        if not self.is_connected():
            print("Not connected.")
            return
        if from_name is None:
            from_name = input("From name ")
        if to_name is None:
            to_name = input("To name ")
        resp = self.send_command(f"RNFR {from_name}")
        if resp.startswith("5"):
            return
        self.send_command(f"RNTO {to_name}")

    def get_info(self):
        data_port = random.randint(1024, 65535)
        local_ip = self.client_socket.getsockname()[0]
        port_command = f"PORT {','.join(local_ip.split('.'))},{
            data_port//256},{data_port % 256}"
        resp = self.send_command(port_command)
        return data_port, local_ip, resp

    def get_data_socket(self, local_ip, data_port):
        data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        data_socket.bind((local_ip, data_port))
        data_socket.listen(1)
        return data_socket

    def calculate_speed(self, start_time, end_time, bytes_transferred):
        transfer_time = end_time - start_time
        transfer_speed = (bytes_transferred/1000) / (transfer_time + 1e-6)
        return transfer_time, transfer_speed

    def close(self, remote_file=None):
        if not self.is_connected():
            print("Not connected.")
        else:
            if not remote_file:
                remote_file = input("Remote file ")
            self.send_command(f"DELE {remote_file}")

    def lcd(self, local_dir=None):
        if local_dir is None:
            local_dir = self.local_dir
        try:
            os.chdir(local_dir)
            print(os.getcwd())
        except FileNotFoundError:
            print(f"{local_dir}: File not found")

    def ls(self, remote_file=None, local_file=None):
        if not self.is_connected():
            print("Not connected.")
            return
        data_port, local_ip, resp = self.get_info()

        if resp.startswith("200"):
            try:
                data_socket = self.get_data_socket(local_ip, data_port)
                if local_file is not None:
                    write_to = os.path.join(os.getcwd(), local_file)
                    try:
                        with open(write_to, 'w'):
                            pass
                    except IOError:
                        data_socket.close()
                        raise Exception(f"Error opening local file {local_file}.\n> {
                                        local_file[0]}:No Such file or directory")

                resp = self.send_command(
                    f'NLST {remote_file}' if remote_file is not None else 'NLST')
                if resp.startswith('5'):
                    data_socket.close()
                    return
                if resp.startswith('1'):
                    data_conn, _ = data_socket.accept()
                    bytes_recv = 0
                    start_time = time.time()

                    while True:
                        data = data_conn.recv(1024)
                        if not data:
                            break

                        if local_file is None:
                            print(data.decode(), end="")
                        else:
                            with open(local_file, 'wb') as f:
                                f.write(data)
                                print(150)

                        bytes_recv += len(data)

                    end_time = time.time()
                    transfer_time, transfer_speed = self.calculate_speed(
                        start_time, end_time, bytes_recv)
                    data_conn.close()
                data_socket.close()
                print(self.client_socket.recv(1024).decode(), end="")
                print(f"ftp: {bytes_recv} bytes sent in {
                      transfer_time:.2f}Seconds {transfer_speed:.2f}KBytes/sec.")
            except Exception as e:
                print(e)
                return

    def get(self, remote_file=None, local_file=None):  # remote to local
        if not self.is_connected():
            print("Not connected.")
            return
        if remote_file is None:
            remote_file = input("Remote file ")
            local_file = input("Local file ")
        if local_file is None:
            local_file = remote_file
        elif local_file.strip() == "":
            local_file = remote_file
        data_port, local_ip, resp = self.get_info()

        if resp.startswith("200"):
            try:
                data_socket = self.get_data_socket(local_ip, data_port)
                resp = self.send_command(f'RETR {remote_file}')
                if resp.startswith('5'):
                    data_socket.close()
                    return

                write_to = os.path.join(os.getcwd(), local_file)
                can_write = 1
                try:
                    with open(write_to, 'wb'):
                        pass
                except:
                    can_write = 0
                    print("> R:No such process")

                if resp.startswith('1') and can_write:
                    data_conn, _ = data_socket.accept()
                    bytes_recv = 0
                    start_time = time.time()

                    while True:
                        data = data_conn.recv(1024)
                        if not data:
                            break

                        if can_write:
                            with open(local_file, 'ab') as f:
                                f.write(data)
                        bytes_recv += len(data)

                    end_time = time.time()
                    transfer_time, transfer_speed = self.calculate_speed(
                        start_time, end_time, bytes_recv)
                    data_conn.close()
                data_socket.close()
                print(self.client_socket.recv(1024).decode(), end="")
                print(f"ftp: {bytes_recv} bytes sent in {
                      transfer_time:.2f}Seconds {transfer_speed:.2f}KBytes/sec.")
            except Exception as e:
                print(e)
                return

    def put(self, local_file=None, remote_file=None):  # local to remote
        if not self.is_connected():
            print("Not connected.")
            return
        if local_file is None:
            local_file = input("Local file ")
            remote_file = input("Remote file ")
        if remote_file is None:
            remote_file = local_file
        elif remote_file.strip() == "":
            remote_file = local_file
        data_port, local_ip, resp = self.get_info()

        if resp.startswith("200"):
            try:
                data_socket = self.get_data_socket(local_ip, data_port)
                resp = self.send_command(f'STOR {remote_file}')

                if resp.startswith('5'):
                    data_socket.close()
                    return

                read_from = os.path.join(os.getcwd(), local_file)
                can_read = 1
                try:
                    with open(read_from, 'rb'):
                        pass
                except:
                    can_read = 0
                    print("> R:No such process")

                if resp.startswith('1') and can_read:
                    data_conn, _ = data_socket.accept()
                    bytes_sent = 0
                    start_time = time.time()

                    with open(local_file, 'rb') as f:
                        while True:
                            data = f.read(1024)
                            if not data:
                                break
                            data_conn.sendall(data)
                            bytes_sent += len(data)

                    end_time = time.time()
                    transfer_time, transfer_speed = self.calculate_speed(
                        start_time, end_time, bytes_sent)
                    data_conn.close()
                data_socket.close()
                print(self.client_socket.recv(1024).decode(), end="")
                print(f"ftp: {bytes_sent} bytes sent in {
                      transfer_time:.2f}Seconds {transfer_speed:.2f}KBytes/sec.")
            except Exception as e:
                print(e)
                return
