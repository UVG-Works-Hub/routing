import yaml
import asyncio
from NetworkClient import NetworkClient
import sys
import logging
import aioconsole

class InteractiveClient:
    def __init__(self):
        self.client = None
        self.config = None
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
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
                "mode": input("Enter mode (lsr or flooding): "),
                "verbose": input("Enable verbose logging? (y/n): ").lower() == 'y'
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
            mode=self.config["mode"],
            verbose=self.config["verbose"]
        )

    async def run_client(self):
        if not self.client:
            self.logger.error("Client not initialized. Please load configuration first.")
            return

        try:
            await self.client.connect_and_process()
        except Exception as e:
            self.logger.error(f"Error in client processing: {str(e)}")

    async def interactive_send(self):
        while True:
            to_jid = await aioconsole.ainput("Enter recipient's JID (or 'quit' to exit): ")
            if to_jid.lower() == 'quit':
                break

            message_type = await aioconsole.ainput("Enter message type (default: message): ") or "message"
            payload = await aioconsole.ainput("Enter message payload: ")
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

        client_task = asyncio.create_task(self.run_client())
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