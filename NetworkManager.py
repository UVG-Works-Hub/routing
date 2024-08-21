import asyncio
import sys
import json
import time
from NetworkClient import Client
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
        await asyncio.sleep(20)  # Increased delay to allow more time for LSR to stabilize

        # Test LSR mode
        self.logger.info("Testing LSR mode...")
        self.logger.info("Sending message from A to D (should go through I)")
        self.send_message(self.clients[0], "dj4tcha21881@alumchat.lol/algorithms", "message", "Test message from A to D")

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
    mode = "lsr"

    clients_params = [
        {"jid": "aj4tcha21881@alumchat.lol/algorithms", "password": "password", "neighbors": ["bj4tcha21881@alumchat.lol/algorithms", "ij4tcha21881@alumchat.lol/algorithms", "cj4tcha21881@alumchat.lol/algorithms"], "costs": {"bj4tcha21881@alumchat.lol/algorithms": 7, "ij4tcha21881@alumchat.lol/algorithms": 1, "cj4tcha21881@alumchat.lol/algorithms": 7}, "mode": mode},
        {"jid": "bj4tcha21881@alumchat.lol/algorithms", "password": "password", "neighbors": ["aj4tcha21881@alumchat.lol/algorithms", "fj4tcha21881@alumchat.lol/algorithms"], "costs": {"aj4tcha21881@alumchat.lol/algorithms": 7, "fj4tcha21881@alumchat.lol/algorithms": 2}, "mode": mode},
        {"jid": "cj4tcha21881@alumchat.lol/algorithms", "password": "password", "neighbors": ["aj4tcha21881@alumchat.lol/algorithms", "dj4tcha21881@alumchat.lol/algorithms"], "costs": {"aj4tcha21881@alumchat.lol/algorithms": 7, "dj4tcha21881@alumchat.lol/algorithms": 5}, "mode": mode},
        {"jid": "dj4tcha21881@alumchat.lol/algorithms", "password": "password", "neighbors": ["fj4tcha21881@alumchat.lol/algorithms", "ij4tcha21881@alumchat.lol/algorithms", "cj4tcha21881@alumchat.lol/algorithms", "ej4tcha21881@alumchat.lol/algorithms"], "costs": {"fj4tcha21881@alumchat.lol/algorithms": 1, "ij4tcha21881@alumchat.lol/algorithms": 6, "cj4tcha21881@alumchat.lol/algorithms": 5, "ej4tcha21881@alumchat.lol/algorithms": 1}, "mode": mode},
        {"jid": "ej4tcha21881@alumchat.lol/algorithms", "password": "password", "neighbors": ["dj4tcha21881@alumchat.lol/algorithms", "gj4tcha21881@alumchat.lol/algorithms"], "costs": {"dj4tcha21881@alumchat.lol/algorithms": 1, "gj4tcha21881@alumchat.lol/algorithms": 4}, "mode": mode},
        {"jid": "fj4tcha21881@alumchat.lol/algorithms", "password": "password", "neighbors": ["hj4tcha21881@alumchat.lol/algorithms", "gj4tcha21881@alumchat.lol/algorithms", "bj4tcha21881@alumchat.lol/algorithms", "dj4tcha21881@alumchat.lol/algorithms"], "costs": {"hj4tcha21881@alumchat.lol/algorithms": 4, "bj4tcha21881@alumchat.lol/algorithms": 2, "gj4tcha21881@alumchat.lol/algorithms": 3, "dj4tcha21881@alumchat.lol/algorithms": 1}, "mode": mode},
        {"jid": "gj4tcha21881@alumchat.lol/algorithms", "password": "password", "neighbors": ["fj4tcha21881@alumchat.lol/algorithms", "ej4tcha21881@alumchat.lol/algorithms"], "costs": {"fj4tcha21881@alumchat.lol/algorithms": 3, "ej4tcha21881@alumchat.lol/algorithms": 4}, "mode": mode},
        {"jid": "hj4tcha21881@alumchat.lol/algorithms", "password": "password", "neighbors": ["fj4tcha21881@alumchat.lol/algorithms"], "costs": {"fj4tcha21881@alumchat.lol/algorithms": 4}, "mode": mode},
        {"jid": "ij4tcha21881@alumchat.lol/algorithms", "password": "password", "neighbors": ["aj4tcha21881@alumchat.lol/algorithms", "dj4tcha21881@alumchat.lol/algorithms"], "costs": {"aj4tcha21881@alumchat.lol/algorithms": 1, "dj4tcha21881@alumchat.lol/algorithms": 6}, "mode": mode},
    ]

    manager = NetworkManager(clients_params)
    manager.run()
