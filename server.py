import socket
import threading
import sympy
import random
import math
import hashlib

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
            client_sock, addr = self.s.accept()
            username = client_sock.recv(1024).decode()
            print(f"{username} tries to connect")

            self.username_lookup[client_sock] = username
            self.clients.append(client_sock)

            client_sock.send(f"{self.e} {self.n}".encode())

            data = client_sock.recv(1024).decode()
            e_c, n_c = map(int, data.split())
            self.public_keys[client_sock] = (e_c, n_c)

            self.broadcast(f"new person has joined: {username}")

            threading.Thread(target=self.handle_client,args=(client_sock,)).start()

    def broadcast(self, msg: str, sender=None):
        hash_val = hashlib.sha256(msg.encode()).hexdigest()
        for client in list(self.clients):
            if client is sender:
                continue
            try:
                e_c, n_c = self.public_keys[client]
                encrypted = [str(pow(ord(ch), e_c, n_c)) for ch in msg]
                message = hash_val + '|' + ' '.join(encrypted)
                client.send(message.encode())
            except Exception as e:
                print(f"[server]: failed to send to {self.username_lookup.get(client, 'unknown')}: {e}")
                self.disconnect(client)

    def handle_client(self, client_sock):
        while True:
            try:
                data = client_sock.recv(4096).decode()
                if not data:
                    break

                hash_val, encrypted_payload = data.split('|', 1)
                parts = encrypted_payload.split()

                decrypted = ''.join(chr(pow(int(num), self.d, self.n)) for num in parts)

                if hashlib.sha256(decrypted.encode()).hexdigest() != hash_val:
                    print("Message failed integrity check")
                    continue

                username = self.username_lookup.get(client_sock, "??")
                print(f"[{username}]: {decrypted}")

                self.broadcast(f"{username}: {decrypted}", sender=client_sock)
            except Exception as e:
                print(f"[server]: error: {e}")
                break

        self.disconnect(client_sock)

    def disconnect(self, client_sock):
        username = self.username_lookup.get(client_sock, "unknown")
        print(f"[server]: {username} disconnected")
        if client_sock in self.clients:
            self.clients.remove(client_sock)
        self.username_lookup.pop(client_sock, None)
        self.public_keys.pop(client_sock, None)
        try:
            client_sock.close()
        except:
            pass

if __name__ == "__main__":
    server = Server(9001)
    server.start()