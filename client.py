import socket
import threading
import math
import sympy
import random

class Client:
    def __init__(self, server_ip: str, port: int, username: str) -> None:
        self.server_ip = server_ip
        self.port = port
        self.username = username


    def init_connection(self):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.s.connect((self.server_ip, self.port))
        except Exception as e:
            print("[client]: could not connect to server: ", e)
            return

        self.s.send(self.username.encode())

        primes = [i for i in range(1000, 5000) if sympy.isprime(i)]
        p, q = random.sample(primes, 2)
        self.n = p * q
        phi = (p - 1) * (q - 1)
        e = 3
        while math.gcd(e, phi) != 1:
            e += 2
        self.e = e
        self.secret = pow(e, -1, phi)

        data = self.s.recv(1024).decode()
        self.e_s, self.n_s = tuple(map(int, data.split()))

        self.s.send(f"{self.e} {self.n}".encode())

        secret_s = int(self.s.recv(1024).decode())
        self.secret_s = pow(secret_s, self.secret, self.n)

        message_handler = threading.Thread(target=self.read_handler,args=())
        message_handler.start()
        input_handler = threading.Thread(target=self.write_handler,args=())
        input_handler.start()

    def read_handler(self): 
        while True:
            message = self.s.recv(1024).decode()
            message = [int(ch) for ch in message.split()]
            message = [chr(pow(c, self.secret, self.n)) for c in message]
            print(''.join(message))

    def write_handler(self):
        while True:
            message = input()
            message = [str(pow(ord(ch), self.e_s,self.n)) for ch in message]
            message =  ' '.join(message)
            self.s.send(message.encode())

if __name__ == "__main__":
    cl = Client("127.0.0.1", 9001, "b_g")
    cl.init_connection()