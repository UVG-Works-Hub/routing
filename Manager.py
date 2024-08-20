import asyncio
import sys
import json
import time
from Client import Client
import logging

class NetworkManager:
    def __init__(self, clients_params):
        self.clients_params = clients_params
        self.clients = []
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("NetworkManager")

    def initialize_clients(self):
        for params in self.clients_params:
            client = Client(
                jid=params["jid"],
                password=params["password"],
                neighbors=params["neighbors"],
                costs=params.get("costs", {}),
                mode=params.get("mode", "lsr")
            )
            self.clients.append(client)

    async def connect_clients(self):
        connect_tasks = []
        for client in self.clients:
            connect_tasks.append(asyncio.create_task(client.connect_and_process()))
        await asyncio.gather(*connect_tasks)

    def send_message(self, from_client, to_client_jid, message_type="message", payload="Hello"):
        message = {
            "type": message_type,
            "from": from_client.boundjid.full,
            "to": to_client_jid,
            "hops": 0,
            "headers": [],
            "payload": payload
        }
        from_client.send_message_to(to_client_jid, json.dumps(message))

    async def simulate_network(self):
        self.logger.info("Starting network simulation...")
        await asyncio.sleep(5)  # Increased delay to allow more time for connections
        if len(self.clients) > 1:
            self.send_message(self.clients[0], self.clients[1].boundjid.bare, "message", "Test message")
        self.logger.info("Network simulation completed.")

    async def run_async(self):
        self.initialize_clients()
        await self.connect_clients()
        await self.simulate_network()
        while True:
            await asyncio.sleep(1)

    def run(self):
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

        try:
            asyncio.run(self.run_async())
        except KeyboardInterrupt:
            self.logger.info("Simulation terminated manually.")

if __name__ == "__main__":
    clients_params = [
        {"jid": "aj4tcha21881@alumchat.lol", "password": "password", "neighbors": ["bj4tcha21881@alumchat.lol", "cj4tcha21881@alumchat.lol"], "costs": {"bj4tcha21881@alumchat.lol": 1, "cj4tcha21881@alumchat.lol": 2}, "mode": "lsr"},
        {"jid": "bj4tcha21881@alumchat.lol", "password": "password", "neighbors": ["aj4tcha21881@alumchat.lol", "ij4tcha21881@alumchat.lol", "fj4tcha21881@alumchat.lol"], "costs": {"aj4tcha21881@alumchat.lol": 1, "ij4tcha21881@alumchat.lol": 1, "fj4tcha21881@alumchat.lol": 1}, "mode": "lsr"},
        {"jid": "cj4tcha21881@alumchat.lol", "password": "password", "neighbors": ["aj4tcha21881@alumchat.lol", "dj4tcha21881@alumchat.lol"], "costs": {"aj4tcha21881@alumchat.lol": 2, "dj4tcha21881@alumchat.lol": 1}, "mode": "lsr"},
        {"jid": "dj4tcha21881@alumchat.lol", "password": "password", "neighbors": ["cj4tcha21881@alumchat.lol", "ej4tcha21881@alumchat.lol", "ij4tcha21881@alumchat.lol"], "costs": {"cj4tcha21881@alumchat.lol": 1, "ej4tcha21881@alumchat.lol": 1, "ij4tcha21881@alumchat.lol": 1}, "mode": "lsr"},
        {"jid": "ej4tcha21881@alumchat.lol", "password": "password", "neighbors": ["dj4tcha21881@alumchat.lol"], "costs": {"dj4tcha21881@alumchat.lol": 1}, "mode": "lsr"},
        {"jid": "fj4tcha21881@alumchat.lol", "password": "password", "neighbors": ["bj4tcha21881@alumchat.lol", "hj4tcha21881@alumchat.lol"], "costs": {"bj4tcha21881@alumchat.lol": 1, "hj4tcha21881@alumchat.lol": 1}, "mode": "lsr"},
        {"jid": "gj4tcha21881@alumchat.lol", "password": "password", "neighbors": ["hj4tcha21881@alumchat.lol"], "costs": {"hj4tcha21881@alumchat.lol": 1}, "mode": "lsr"},
        {"jid": "hj4tcha21881@alumchat.lol", "password": "password", "neighbors": ["fj4tcha21881@alumchat.lol", "gj4tcha21881@alumchat.lol"], "costs": {"fj4tcha21881@alumchat.lol": 1, "gj4tcha21881@alumchat.lol": 1}, "mode": "lsr"},
        {"jid": "ij4tcha21881@alumchat.lol", "password": "password", "neighbors": ["bj4tcha21881@alumchat.lol", "dj4tcha21881@alumchat.lol"], "costs": {"bj4tcha21881@alumchat.lol": 1, "dj4tcha21881@alumchat.lol": 1}, "mode": "lsr"},
    ]

    manager = NetworkManager(clients_params)
    manager.run()
