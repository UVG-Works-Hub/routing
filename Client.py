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

    def send_message_to(self, to_jid, message, msg_type='chat'):
        if isinstance(message, str):
            message = json.loads(message)

        if message['type'] == 'link_state':
            # Link state messages are sent directly to neighbors
            self.send_message(mto=to_jid, mbody=json.dumps(message), mtype=msg_type)
            self.logger.info(f"Sent a link state message to {to_jid}")
        else:
            # For other messages, use the routing table
            next_hop = self.get_next_hop(to_jid)
            if next_hop:
                message['hops'] = message.get('hops', 0) + 1
                message['path'] = message.get('path', []) + [self.boundjid.bare]
                self.send_message(mto=next_hop, mbody=json.dumps(message), mtype=msg_type)
                self.logger.info(f"Forwarded message to {to_jid} via {next_hop}")
            else:
                self.logger.error(f"No route to {to_jid}")

    def get_next_hop(self, destination):
        print(self.routing_table)
        return self.routing_table.get(destination, (None, None))[0]

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

        self.logger.info(f"Link State Database: {self.link_state_db}")
        self.logger.info(f"Computed Routing Table: {self.routing_table}")

    def message(self, msg):
        if msg['type'] in ('chat', 'normal'):
            try:
                message_body = json.loads(msg['body'])
                if isinstance(message_body, dict):
                    if message_body.get("type") == "link_state":
                        self.logger.info(f"Received link state info from {message_body['from']}")
                        self.link_state_db[message_body["from"]] = message_body["state"]
                        self.compute_routing_table()
                    else:
                        self.logger.info(f"Received a message from {msg['from']}")
                        if message_body['to'] == self.boundjid.bare:
                            message_body['path'] = message_body.get('path', []) + [self.boundjid.bare]
                            self.logger.info(f"Message reached its destination: {message_body}")
                            self.logger.info(f"Path taken: {' -> '.join(message_body['path'])}")
                            self.logger.info(f"Number of hops: {message_body['hops']}")
                        else:
                            self.send_message_to(message_body['to'], message_body)
            except json.JSONDecodeError:
                self.logger.info(f"Received a non-JSON message from {msg['from']}: {msg['body']}")

    async def connect_and_process(self):
        self.logger.info(f"Connecting to {self.boundjid.host}...")
        self.connect((self.boundjid.host, 7070), disable_starttls=True)

        try:
            self.logger.info("Connection successful")
            await self.process(forever=True)
        except Exception as e:
            self.logger.error(f"An error occurred: {str(e)}")
