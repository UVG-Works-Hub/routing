import sys
import asyncio
import slixmpp
import json
import heapq
import logging

class Client(slixmpp.ClientXMPP):
    def __init__(self, jid, password, neighbors, costs=None, mode="lsr"):
        super().__init__(jid, password)
        self.neighbors = neighbors
        self.costs = costs or {}
        self.routing_table = {}
        self.link_state_db = {self.boundjid.bare: self.costs}
        self.received_messages = set()
        self.mode = mode

        # Set up logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(self.boundjid.bare)

        self.add_event_handler("session_start", self.start)
        self.add_event_handler("message", self.message)

    async def start(self, event):
        self.logger.info("Session started")
        self.send_presence()
        await self.get_roster()
        self.share_link_state()

    def send_message_to(self, recipient, message, msg_type='chat'):
        self.send_message(mto=recipient, mbody=json.dumps(message), mtype=msg_type)
        self.logger.info(f"Sent a message to {recipient}")

    def flood_message(self, message, sender):
        if message['id'] not in self.received_messages:
            self.received_messages.add(message['id'])
            for neighbor in self.neighbors:
                if neighbor != sender:
                    self.send_message_to(neighbor, message)

    def share_link_state(self):
        message = {
            "type": "link_state",
            "from": self.boundjid.bare,
            "state": self.costs,
            "id": f"ls_{self.boundjid.bare}_{len(self.link_state_db)}"
        }
        for neighbor in self.neighbors:
            self.send_message_to(neighbor, message)
        self.logger.info("Shared link state")

    def compute_routing_table(self):
        self.logger.info("Computing routing table")
        self.routing_table = {}
        pq = [(0, self.boundjid.bare)]
        distances = {self.boundjid.bare: 0}
        previous_nodes = {}

        while pq:
            current_distance, current_node = heapq.heappop(pq)
            if current_distance > distances.get(current_node, float('inf')):
                continue
            for neighbor, cost in self.link_state_db.get(current_node, {}).items():
                distance = current_distance + cost
                if distance < distances.get(neighbor, float('inf')):
                    distances[neighbor] = distance
                    heapq.heappush(pq, (distance, neighbor))
                    previous_nodes[neighbor] = current_node

        for node in distances:
            if node == self.boundjid.bare:
                continue
            path = []
            current = node
            while current != self.boundjid.bare:
                path.insert(0, current)
                current = previous_nodes.get(current)
                if current is None:
                    break
            if path:
                self.routing_table[node] = (path[0], distances[node])

        self.logger.info(f"Updated routing table: {self.routing_table}")

    def message(self, msg):
        if msg['type'] in ('chat', 'normal'):
            try:
                message_body = json.loads(msg['body'])
                if isinstance(message_body, dict) and message_body.get("type") == "link_state":
                    self.logger.info(f"Received link state info from {message_body['from']}")
                    self.link_state_db[message_body["from"]] = message_body["state"]
                    self.compute_routing_table()
                else:
                    self.logger.info(f"Received a message from {msg['from']}")
                    if self.mode == "flooding":
                        self.flood_message(message_body, msg['from'].bare)
            except json.JSONDecodeError:
                self.logger.info(f"Received a non-JSON message from {msg['from']}: {msg['body']}")

    async def connect_and_process(self):
        self.logger.info(f"Connecting to {self.boundjid.host}...")
        self.connect((self.boundjid.host, 7070), disable_starttls=True)

        try:
            self.logger.info("Connection successful")
            await self.process(forever=False)
        except Exception as e:
            self.logger.error(f"An error occurred: {str(e)}")
