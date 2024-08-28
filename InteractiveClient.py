import yaml
import asyncio
from NetworkClient import NetworkClient
class InteractiveClient:
    def __init__(self):
        self.client = None
        self.config = None
    # Load configuration from a YAML file or manually
    def load_config(self, config_file=None):
        if config_file: # Load from file
            with open(config_file, 'r') as file: # Load from file
                self.config = yaml.safe_load(file)
        else: 
            self.config = {
                "jid": input("Enter JID: "),
                "password": input("Enter password: "),
                "neighbors": input("Enter neighbors (comma-separated): ").split(','),
                "costs": {},
                "mode": input("Enter mode (lsr or flooding): ")
            }
            for neighbor in self.config["neighbors"]: # Load costs manually for each neighbor
                cost = int(input(f"Enter cost for {neighbor}: ")) # Load costs manually for each neighbor
                self.config["costs"][neighbor] = cost # Load costs manually for each neighbor

    def initialize_client(self): # Initialize the client with the loaded configuration
        self.client = NetworkClient(
            jid=self.config["jid"],
            password=self.config["password"],
            neighbors=self.config["neighbors"],
            costs=self.config["costs"],
            mode=self.config["mode"]
        )

    async def run(self): # Connect and process messages
        if not self.client: # Check if client is initialized
            print("Client not initialized. Please load configuration first.")
            return

        await self.client.connect_and_process() # Await connection and processing of messages

    async def interactive_send(self): # Interactive message sending
        while True: # Loop until user quits
            to_jid = input("Enter recipient's JID (or 'quit' to exit): ") # Get recipient's JID
            if to_jid.lower() == 'quit': # Check if user wants to quit
                break

            message_type = input("Enter message type (default: message): ") or "message" # Get message type
            payload = input("Enter message payload: ") # Get message payload
            # Send message to recipient
            self.client.send_message_to(to_jid, {
                "type": message_type,
                "from": self.client.boundjid.full,
                "to": to_jid,
                "payload": payload
            })
            print(f"Message sent to {to_jid}")

    async def main(self): # Main function to run the client
        config_file = input("Enter path to YAML config file (or press Enter for manual input): ") # Get path to YAML config file
        self.load_config(config_file if config_file else None) # Load configuration
        self.initialize_client() # Initialize client

        client_task = asyncio.create_task(self.run()) # Create task to run the client
        interactive_task = asyncio.create_task(self.interactive_send()) # Create task for interactive message sending

        await asyncio.gather(client_task, interactive_task) # Await both tasks to complete

if __name__ == "__main__":
    wrapper = InteractiveClient() # Create an instance of InteractiveClient
    asyncio.run(wrapper.main()) # Run the main function
