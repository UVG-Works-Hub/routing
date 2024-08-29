import yaml
import asyncio
from NetworkClient import NetworkClient
import sys
import logging

class InteractiveClient:
    def __init__(self):
        self.client = None
        self.config = None
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("InteractiveClient")

    def load_config(self, config_file=None):
        if config_file:
            with open(config_file, 'r') as file:
                self.config = yaml.safe_load(file)
        else:
            self.config = {
                "jid": input("Enter JID: "),
                "password": input("Enter password: "),
                "neighbors": input("Enter neighbors (comma-separated): ").split(','),
                "costs": {},
                "mode": input("Enter mode (lsr or flooding): ")
            }
            for neighbor in self.config["neighbors"]:
                cost = int(input(f"Enter cost for {neighbor}: "))
                self.config["costs"][neighbor] = cost

    def initialize_client(self):
        self.logger.info("Initializing client...")
        self.logger.info(f"Config: {self.config}")
        self.client = NetworkClient(
            jid=self.config["jid"],
            password=self.config["password"],
            neighbors=self.config["neighbors"],
            costs=self.config["costs"],
            mode=self.config["mode"]
        )

    async def run(self):
        if not self.client:
            self.logger.error("Client not initialized. Please load configuration first.")
            return

        try:
            await self.client.connect_and_process()
        except Exception as e:
            self.logger.error(f"Error in client processing: {str(e)}")

    async def interactive_send(self):
        while True:
            await asyncio.sleep(0.1)  # Small delay to allow other tasks to run
            to_jid = input("Enter recipient's JID (or 'quit' to exit): ")
            if to_jid.lower() == 'quit':
                break

            message_type = input("Enter message type (default: message): ") or "message"
            payload = input("Enter message payload: ")
            await self.client.send_message_to(to_jid, {
                "type": message_type,
                "from": self.client.boundjid.full,
                "to": to_jid,
                "payload": payload,
                "hops": 0,
                "headers": []
            })
            self.logger.info(f"Message sent to {to_jid}")

    async def main(self):
        config_file = input("Enter path to YAML config file (or press Enter for manual input): ")
        self.load_config(config_file if config_file else None)
        self.initialize_client()

        client_task = asyncio.create_task(self.run())

        # Wait for the client to connect before starting the interactive send
        await asyncio.sleep(5)  # Give more time for the client to connect and initialize

        interactive_task = asyncio.create_task(self.interactive_send())

        await asyncio.gather(client_task, interactive_task)

if __name__ == "__main__":
    wrapper = InteractiveClient()

    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    try:
        asyncio.run(wrapper.main())
    except KeyboardInterrupt:
        print("Exiting...")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
