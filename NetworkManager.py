# Import needed libraries
import asyncio
import sys
import json
import time
import logging

# Import NetworkClient class from NetworkClient.py
from NetworkClient import NetworkClient as Client


class NetworkManager:
    """
    Class in charge of managing multiple clients and simulating a network.
    """
    def __init__(self, clients_params):
        """
        Constructor for NetworkManager class.
        :param clients_params: List of users, passwords, neighbors and costs.
        """
        self.clients_params = clients_params
        # List of clients
        self.clients = []
        # Initialize login basic configuration
        logging.basicConfig(level=logging.INFO)
        # Create logger
        self.logger = logging.getLogger("NetworkManager")

    def initialize_clients(self):
        """
        Initialize clients based on the parameters provided.
        """
        # Create clients based on the parameters provided
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
        """
        Connect all clients and start processing messages.
        """
        connect_tasks = []
        # Connect all clients
        for client in self.clients:
            # Create a task for each client
            connect_tasks.append(asyncio.create_task(client.connect_and_process()))
        # Wait for all clients to connect
        await asyncio.gather(*connect_tasks)

    def send_message(self, from_client, to_client_jid, message_type="message", payload="Hello"):
        """
        Method use to send a message from one client to another.
        :param from_client: Client sending the message.
        :param to_client_jid: JID of the client receiving the message.
        :param message_type: Type of message.
        :param payload: Payload of the message.
        """
        # Message structure
        message = {
            "type": message_type,
            "from": from_client.boundjid.full,
            "to": to_client_jid,
            "hops": 0,
            "headers": [],
            "payload": payload
        }
        # Send message
        from_client.send_message_to(to_client_jid, json.dumps(message))

    async def simulate_network(self):
        """
        Simulate network by sending messages between clients.
        """
        # Announce start of simulation
        self.logger.info("Starting network simulation...")
        # Wait for clients to stabilize
        await asyncio.sleep(20)  # Increased delay to allow more time for LSR to stabilize

        # Test LSR mode
        self.logger.info("Testing LSR mode...")
        # Send message from A to D
        self.logger.info("Sending message from A to D (should go through I)")
        # Send message from A to D
        self.send_message(self.clients[0], "dj4tcha21881@alumchat.lol/algorithms", "message", "Test message from A to D")
        # Wait for message to be delivered
        self.logger.info("Network simulation completed.")

    async def run_async(self):
        """
        Run the simulation asynchronously.
        """
        # Initialize clients
        self.initialize_clients()
        # Connect clients to server
        await self.connect_clients()
        # Simulate network in server
        await self.simulate_network()
        # Keep running while waiting for messages
        while True:
            # Wait for 1 second
            await asyncio.sleep(1)

    def run(self):
        """
        Start simulation.
        """
        # Add condition to run on Windows
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

        try:
            # Run the simulation
            asyncio.run(self.run_async())
        except KeyboardInterrupt:
            self.logger.info("Simulation terminated manually.")

if __name__ == "__main__":
    # Define mode
    mode = "lsr"
    # Define clients parameters
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

    # Create NetworkManager object
    manager = NetworkManager(clients_params)
    # Run simulation
    manager.run()
