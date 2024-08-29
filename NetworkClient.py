import sys
import asyncio
import slixmpp
import json
import heapq
import logging
import time
import uuid

class NetworkClient(slixmpp.ClientXMPP):
    def __init__(self, jid, password, neighbors, costs=None, mode="lsr", verbose=False):
        super().__init__(jid, password)
        self.use_starttls = False
        self.register_plugin('feature_starttls', module='slixmpp.features.feature_starttls')
        self.neighbors = neighbors
        self.costs = costs or {}
        self.routing_table = {}
        self.link_state_db = {self.boundjid.full: self.costs}
        self.received_messages = {}
        self.mode = mode
        self.sequence_number = 0
        self.verbose = verbose

        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(self.boundjid.full)

        self.add_event_handler("session_start", self.start)
        self.add_event_handler("message", self.message)

    def log(self, level, message):
        if self.verbose or level in ['IMPORTANT', 'CRITICAL', 'ERROR']:
            if level.lower() == 'important':
                level = 'INFO'
            getattr(self.logger, level.lower())(message)

    async def start(self, event):
        self.log('INFO', f"Session started (Mode: {self.mode})")
        self.send_presence()
        await self.get_roster()
        await asyncio.sleep(1)
        await self.discover_neighbors()
        if self.mode == "lsr":
            await self.share_link_state()

    async def send_message_to(self, to_jid, message, msg_type='chat'):
        if isinstance(message, str):
            message = json.loads(message)

        if 'id' not in message:
            message['id'] = str(uuid.uuid4())

        if message['type'] in ['echo', 'info']:
            self.send_message(mto=to_jid, mbody=json.dumps(message), mtype=msg_type)
            self.log('INFO', f"Sent a {message['type']} message to {to_jid}")
        else:
            if self.mode == "lsr":
                next_hop = self.get_next_hop(to_jid)
                if next_hop:
                    message['hops'] += 1
                    message['headers'].append({"via": self.boundjid.full})
                    self.send_message(mto=next_hop, mbody=json.dumps(message), mtype=msg_type)
                    self.log('IMPORTANT', f"Forwarded message to {to_jid} via {next_hop}")
                else:
                    self.log('ERROR', f"No route to {to_jid}")
            elif self.mode == "flooding":
                self.log('IMPORTANT', f"Initiating flood for message: {message.get('id', 'unknown')}")
                await self.flood_message(message, self.boundjid.full)

    def message(self, msg):
        if msg['type'] in ('chat', 'normal'):
            try:
                message_body = json.loads(msg['body'])
                if isinstance(message_body, dict):
                    if message_body.get("type") == "info":
                        asyncio.create_task(self.flood_message(message_body, msg['from'].full))
                        self.link_state_db[message_body["from"]] = json.loads(message_body["payload"])
                        self.compute_routing_table()
                    elif message_body.get("type") == "echo":
                        self.handle_echo(message_body)
                    else:
                        self.log('IMPORTANT', f"Received a message from {msg['from']}: {message_body.get('id', 'unknown')}")
                        if message_body['to'] == self.boundjid.full:
                            self.log('IMPORTANT', f"Message reached its destination: {message_body.get('payload', 'unknown')}")
                            self.log('IMPORTANT', f"Path taken: {' -> '.join([h['via'] for h in message_body['headers']])}")
                            self.log('IMPORTANT', f"Number of hops: {message_body['hops']}")
                        else:
                            if self.mode == "flooding":
                                asyncio.create_task(self.flood_message(message_body, msg['from'].full))
                            else:
                                asyncio.create_task(self.send_message_to(message_body['to'], message_body))
            except json.JSONDecodeError:
                self.log('INFO', f"Received a non-JSON message from {msg['from']}: {msg['body']}")

    async def discover_neighbors(self):
        for neighbor in self.neighbors:
            await self.send_echo(neighbor)

    async def send_echo(self, to_jid):
        message = {
            "type": "echo",
            "from": self.boundjid.full,
            "to": to_jid,
            "hops": 0,
            "headers": [],
            "payload": str(time.time()),
            "id": str(uuid.uuid4())
        }
        await self.send_message_to(to_jid, json.dumps(message))


    def get_next_hop(self, destination):
        return self.routing_table.get(destination, (None, None))[0]

    async def flood_message(self, message, sender):
        if message['id'] not in self.received_messages:
            self.received_messages[message['id']] = time.time()
            self.log('INFO', f"Received flood message: {message.get('id', 'unknown')}")

            if self.boundjid.full not in [header['via'] for header in message['headers']]:
                message['hops'] += 1
                message['headers'].append({"via": self.boundjid.full})

                for neighbor in self.neighbors:
                    if neighbor != sender and neighbor not in [header['via'] for header in message['headers']]:
                        self.send_message(mto=neighbor, mbody=json.dumps(message), mtype='chat')
                        self.log('INFO', f"Forwarded flood message to {neighbor}")
            else:
                self.log('IMPORTANT', f"Stopping flood: node {self.boundjid.full} already in path")

    async def share_link_state(self):
        self.sequence_number += 1
        message = {
            "type": "info",
            "from": self.boundjid.full,
            "to": "all",
            "hops": 0,
            "headers": [],
            "payload": json.dumps(self.costs),
            "id": f"ls_{self.boundjid.full}_{self.sequence_number}"
        }
        for neighbor in self.neighbors:
            await self.send_message_to(neighbor, message)
        self.log('INFO', "Shared link state")

    def compute_routing_table(self):
        self.log('INFO', "Computing routing table")
        self.routing_table = {}
        pq = [(0, self.boundjid.full)]
        distances = {self.boundjid.full: 0}
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
            if node == self.boundjid.full:
                continue
            path = []
            current = node
            while current != self.boundjid.full:
                path.insert(0, current)
                current = previous_nodes.get(current)
                if current is None:
                    break
            if path:
                self.routing_table[node] = (path[0], distances[node])

        self.log("INFO", f"Link State Database: {self.link_state_db}")
        self.log("INFO", f"Computed Routing Table: {self.routing_table}")

    def handle_echo(self, message):
        if message['to'] == self.boundjid.full:
            rtt = time.time() - float(message['payload'])
            self.log('INFO', f"ECHO reply from {message['from']}, RTT: {rtt:.3f} seconds")
        else:
            asyncio.create_task(self.send_message_to(message['to'], message))

    def schedule_periodic_tasks(self):
        asyncio.create_task(self.periodic_share_link_state())

    async def periodic_share_link_state(self):
        while True:
            await asyncio.sleep(30)  # Share link state every 30 seconds
            if self.mode == "lsr":
                await self.share_link_state()

    async def connect_and_process(self):
        self.log('INFO', f"Important: Connecting to {self.boundjid.host}...")
        self.connect((self.boundjid.host, 7070), disable_starttls=True)

        try:
            self.log('INFO', "Important: Connection successful")
            await self.process(forever=False)
        except Exception as e:
            pass
            # self.log('ERROR', f"An error occurred: {str(e)}")
