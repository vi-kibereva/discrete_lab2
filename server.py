import socket
import threading
import sympy
import random
import math

class Server:

    def __init__(self, port: int) -> None:
        self.host = '127.0.0.1'
        self.port = port
        self.clients = []
        self.username_lookup = {}
        self.public_keys = {}
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.e, self.d, self.n = self.generate_rsa_keys()

    def generate_rsa_keys(self):
        primes = [i for i in range(1000, 5000) if sympy.isprime(i)]
        p, q = random.sample(primes, 2)
        n = p * q
        phi = (p - 1) * (q - 1)
        e = 3
        while math.gcd(e, phi) != 1:
            e += 2
        d = pow(e, -1, phi)
        return e, d, n

    def start(self):
        self.s.bind((self.host, self.port))
        self.s.listen(100)

        print(f"[server]: Listening on {self.host}:{self.port}")

        while True:
            c, addr = self.s.accept()
            username = c.recv(1024).decode()
            print(f"{username} tries to connect")

            self.username_lookup[c] = username
            self.clients.append(c)

            # send public key to the client
            c.send(f"{self.e} {self.n}".encode())

            # receive client's public key
            client_key = c.recv(1024).decode()
            e_c, n_c = map(int, client_key.split())
            self.public_keys[c] = (e_c, n_c)

            self.broadcast(f"new person has joined: {username}")

            threading.Thread(target=self.handle_client, args=(c, addr)).start()

    def broadcast(self, msg: str, sender=None):
        for client in self.clients:
            if client == sender:
                continue

            try:
                e_c, n_c = self.public_keys[client]
                encrypted = [str(pow(ord(ch), e_c, n_c)) for ch in msg]
                encrypted_msg = ' '.join(encrypted)
                client.send(encrypted_msg.encode())
            except Exception as e:
                print(f"[server]: failed to send to {self.username_lookup.get(client, 'unknown')}: {e}")
                self.disconnect(client)

    def handle_client(self, c: socket.socket, addr):
        while True:
            try:
                data = c.recv(4096).decode()
                if not data:
                    break

                decrypted_chars = [
                    chr(pow(int(part), self.d, self.n))
                    for part in data.split()
                ]
                message = ''.join(decrypted_chars)
                username = self.username_lookup.get(c, "???")
                print(f"[{username}]: {message}")

                self.broadcast(f"{username}: {message}", sender=c)

            except Exception as e:
                print(f"[server]: error: {e}")
                break

        self.disconnect(c)

    def disconnect(self, client):
        username = self.username_lookup.get(client, "unknown")
        print(f"[server]: {username} disconnected")
        if client in self.clients:
            self.clients.remove(client)
        self.username_lookup.pop(client, None)
        self.public_keys.pop(client, None)
        try:
            client.close()
        except:
            pass

if __name__ == "__main__":
    s = Server(9001)
    s.start()
