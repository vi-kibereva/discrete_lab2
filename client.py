import socket
import random
import threading
import math
import sympy
import hashlib

class Client:
    def __init__(self, server_ip: str, port: int, username: str) -> None:
        self.server_ip = server_ip
        self.port = port
        self.username = username
        self.e, self.d, self.n = self.generate_keys()

    def generate_keys(self):
        primes = [i for i in range(1000, 5000) if sympy.isprime(i)]
        p, q = random.sample(primes, 2)
        n = p * q
        phi = (p - 1) * (q - 1)
        e = 3
        while math.gcd(e, phi) != 1:
            e += 2
        d = pow(e, -1, phi)
        return e, d, n

    def init_connection(self):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.s.connect((self.server_ip, self.port))
        except Exception as e:
            print(f"[client]: could not connect to server: {e}")
            return
        self.s.send(self.username.encode())
        data = self.s.recv(1024).decode()
        self.e_s, self.n_s = map(int, data.split())

        self.s.send(f"{self.e} {self.n}".encode())

        reader = threading.Thread(target=self.read_handler)
        writer = threading.Thread(target=self.write_handler)
        reader.start()
        writer.start()

        reader.join()
        writer.join()
    def read_handler(self):
        while True:
            try:
                data = self.s.recv(4096).decode()
                if not data:
                    break

                message_hash, message = data.split('|', 1)
                parts = message.split()

                decrypted = ''.join(chr(pow(int(num), self.d, self.n)) for num in parts)

                assert hashlib.sha256(decrypted.encode()).hexdigest() == message_hash, 'Integrity test failed'
                print(decrypted)
            except Exception as e:
                print(f"[client]: Error reading message: {e}")
                break

    def write_handler(self):
        while True:
            try:
                message = input()
                message_hash = hashlib.sha256(message.encode()).hexdigest()
                message = [str(pow(ord(ch), self.e_s, self.n_s)) for ch in message]
                message = message_hash + '|' + ' '.join(message)
                self.s.send(message.encode())
            except Exception as e:
                print(f"[client]: Error sending message: {e}")
                break

if __name__ == "__main__":
    # adjust server_ip, port, username as needed
    cl = Client("127.0.0.1", 9001, "b_g")
    cl.init_connection()