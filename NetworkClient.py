import sys
import asyncio
import slixmpp
import json
import heapq
import logging
import time
# NetworkClient class definition
class NetworkClient(slixmpp.ClientXMPP): # NetworkClient class inherits from slixmpp.ClientXMPP
    def __init__(self, jid, password, neighbors, costs=None, mode="lsr"): # Constructor with JID, password, neighbors, costs, and mode
        super().__init__(jid, password) # Call the constructor of the parent class
        self.neighbors = neighbors # Set the neighbors
        self.costs = costs or {} # Set the costs
        self.routing_table = {} # Initialize the routing table
        self.link_state_db = {self.boundjid.full: self.costs} # Initialize the link state database
        self.received_messages = set() # Initialize the set of received messages
        self.mode = mode # Set the mode

        logging.basicConfig(level=logging.INFO) # Set logging level to INFO
        self.logger = logging.getLogger(self.boundjid.full) # Get logger for the client

        self.add_event_handler("session_start", self.start) # Add event handler for session start
        self.add_event_handler("message", self.message) # Add event handler for message

    async def start(self, event): # Start the session
        self.logger.info(f"Session started (Mode: {self.mode})") # Log session start
        self.send_presence() # Send presence
        await self.get_roster() # Get roster
        await asyncio.sleep(1) # Sleep for 1 second
        self.discover_neighbors() # Discover neighbors
        if self.mode == "lsr": # If mode is LSR
            self.share_link_state() # Share link state

    def discover_neighbors(self): # Discover neighbors
        for neighbor in self.neighbors: # Iterate over neighbors
            self.send_echo(neighbor) # Send echo to neighbor

    def send_echo(self, to_jid): # Send echo message to a JID (to_jid)
        message = {
            "type": "echo",
            "from": self.boundjid.full,
            "to": to_jid,
            "hops": 0,
            "headers": [],
            "payload": str(time.time())
        }
        self.send_message_to(to_jid, json.dumps(message)) # Send message to JID

    def send_message_to(self, to_jid, message, msg_type='chat'): # Send message to a JID (to_jid)
        if isinstance(message, str): # Check if message is a string
            message = json.loads(message) # Parse message as JSON

        if message['type'] in ['echo', 'info']: # Check if message type is echo or info
            self.send_message(mto=to_jid, mbody=json.dumps(message), mtype=msg_type) # Send message to JID
            self.logger.info(f"Sent a {message['type']} message to {to_jid}") # Log message sent to JID
        else:
            if self.mode == "lsr": # If mode is LSR
                next_hop = self.get_next_hop(to_jid) # Get next hop
                if next_hop: # Check if next hop is available
                    message['hops'] += 1 # Increment hops
                    message['headers'].append({"via": self.boundjid.full}) # Append header
                    self.send_message(mto=next_hop, mbody=json.dumps(message), mtype=msg_type) # Send message to next hop
                    self.logger.info(f"Forwarded message to {to_jid} via {next_hop}") # Log message forwarded to JID
                else:
                    self.logger.error(f"No route to {to_jid}") # Log error: no route to JID
            elif self.mode == "flooding": # If mode is flooding
                self.logger.info(f"Initiating flood for message: {message}") # Log initiating flood
                self.flood_message(message, self.boundjid.full) # Flood message

    def get_next_hop(self, destination): # Get next hop for a destination
        return self.routing_table.get(destination, (None, None))[0] # Return next hop from routing table

    def flood_message(self, message, sender): # Flood a message to neighbors
        message_id = f"{message['from']}_{message['to']}_{message.get('payload', '')}"
        if message_id not in self.received_messages: # Check if message is not received
            self.received_messages.add(message_id) # Add message to received messages
            self.logger.info(f"Flooding message: {message}") # Log flooding message

            # Check if this node is already in the path
            if self.boundjid.full not in [header['via'] for header in message['headers']]:
                message['hops'] += 1 # Increment hops
                message['headers'].append({"via": self.boundjid.full}) # Append header

                for neighbor in self.neighbors: # Iterate over neighbors
                    if neighbor != sender and neighbor not in [header['via'] for header in message['headers']]: # Check if neighbor is not sender and not in headers
                        self.send_message(mto=neighbor, mbody=json.dumps(message), mtype='chat') # Send message to neighbor
                        self.logger.info(f"Forwarded flood message to {neighbor}") # Log forwarded flood message
            else:
                self.logger.info(f"Stopping flood: node {self.boundjid.full} already in path") # Log stopping flood

    def share_link_state(self): # Share link state with neighbors (LSR mode) 
        message = {
            "type": "info",
            "from": self.boundjid.full,
            "to": "all",
            "hops": 0,
            "headers": [],
            "payload": json.dumps(self.costs),
            "id": f"ls_{self.boundjid.full}_{len(self.link_state_db)}"
        }
        for neighbor in self.neighbors: # Iterate over neighbors
            self.send_message_to(neighbor, message) # Send message to neighbor
        self.logger.info("Shared link state") # Log shared link state

    def compute_routing_table(self): # Compute routing table
        self.logger.info("Computing routing table") # Log computing routing table
        self.routing_table = {} # Initialize routing table
        pq = [(0, self.boundjid.full)] # Initialize priority queue
        distances = {self.boundjid.full: 0} # Initialize distances
        previous_nodes = {} # Initialize previous nodes

        while pq:
            current_distance, current_node = heapq.heappop(pq) # Pop from priority queue
            if current_distance > distances.get(current_node, float('inf')): # Check if current distance is greater than current node
                continue
            for neighbor, cost in self.link_state_db.get(current_node, {}).items(): # Iterate over neighbors and costs
                distance = current_distance + cost # Calculate distance
                if distance < distances.get(neighbor, float('inf')): # Check if distance is less than neighbor
                    distances[neighbor] = distance # Update distance
                    heapq.heappush(pq, (distance, neighbor)) # Push to priority queue
                    previous_nodes[neighbor] = current_node # Update previous nodes

        for node in distances: # Iterate over distances
            if node == self.boundjid.full: # Check if node is current node
                continue
            path = [] # Initialize path
            current = node # Set current node
            while current != self.boundjid.full: # Loop until current node is current node
                path.insert(0, current) # Insert current node to path
                current = previous_nodes.get(current) # Get previous node
                if current is None:
                    break
            if path:
                self.routing_table[node] = (path[0], distances[node]) # Update routing table

        self.logger.info(f"Link State Database: {self.link_state_db}") # Log link state database
        self.logger.info(f"Computed Routing Table: {self.routing_table}") # Log computed routing table

    def message(self, msg): # Handle incoming messages
        if msg['type'] in ('chat', 'normal'): # Check if message type is chat or normal
            try:
                message_body = json.loads(msg['body']) # Parse message body as JSON
                if isinstance(message_body, dict): # Check if message body is a dictionary
                    if message_body.get("type") == "info": # Check if message type is info
                        self.logger.info(f"Received link state info from {message_body['from']}") # Log received link state info
                        self.flood_message(message_body, msg['from'].full) # Flood message
                        self.link_state_db[message_body["from"]] = json.loads(message_body["payload"]) # Update link state database
                        self.compute_routing_table() # Compute routing table
                    elif message_body.get("type") == "echo": # Check if message type is echo
                        self.handle_echo(message_body) # Handle echo message
                    else:
                        self.logger.info(f"Received a message from {msg['from']}: {message_body}")  # Log received message
                        if message_body['to'] == self.boundjid.full: # Check if message is for current node
                            self.logger.info(f"Message reached its destination: {message_body}") # Log message reached destination
                            self.logger.info(f"Path taken: {' -> '.join([h['via'] for h in message_body['headers']])}") # Log path taken
                            self.logger.info(f"Number of hops: {message_body['hops']}") # Log number of hops
                        else:
                            if self.mode == "flooding": # Check if mode is flooding
                                self.flood_message(message_body, msg['from'].full) # Flood message
                            else:
                                self.send_message_to(message_body['to'], message_body) # Send message to recipient
            except json.JSONDecodeError:
                self.logger.info(f"Received a non-JSON message from {msg['from']}: {msg['body']}") # Log received non-JSON message

    def handle_echo(self, message):
        if message['to'] == self.boundjid.full: # Check if message is for current node
            # Calculate round-trip time
            rtt = time.time() - float(message['payload'])
            self.logger.info(f"ECHO reply from {message['from']}, RTT: {rtt:.3f} seconds") # Log echo reply
        else:
            # Forward the echo message
            self.send_message_to(message['to'], message)

    async def connect_and_process(self): # Connect and process messages
        self.logger.info(f"Connecting to {self.boundjid.host}...") # Log connecting to host
        self.connect((self.boundjid.host, 7070), disable_starttls=True) # Connect to host

        try:
            self.logger.info("Connection successful") # Log connection successful
            await self.process(forever=True) # Process messages forever
        except Exception as e:
            # self.logger.error(f"An error occurred: {str(e)}")
            pass
