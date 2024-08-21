import yaml
import asyncio
from NetworkClient import NetworkClient
class InteractiveClient:
    def __init__(self):
        self.client = None
        self.config = None

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
        self.client = NetworkClient(
            jid=self.config["jid"],
            password=self.config["password"],
            neighbors=self.config["neighbors"],
            costs=self.config["costs"],
            mode=self.config["mode"]
        )

    async def run(self):
        if not self.client:
            print("Client not initialized. Please load configuration first.")
            return

        await self.client.connect_and_process()

    async def interactive_send(self):
        while True:
            to_jid = input("Enter recipient's JID (or 'quit' to exit): ")
            if to_jid.lower() == 'quit':
                break

            message_type = input("Enter message type (default: message): ") or "message"
            payload = input("Enter message payload: ")

            self.client.send_message_to(to_jid, {
                "type": message_type,
                "from": self.client.boundjid.full,
                "to": to_jid,
                "payload": payload
            })
            print(f"Message sent to {to_jid}")

    async def main(self):
        config_file = input("Enter path to YAML config file (or press Enter for manual input): ")
        self.load_config(config_file if config_file else None)
        self.initialize_client()

        client_task = asyncio.create_task(self.run())
        interactive_task = asyncio.create_task(self.interactive_send())

        await asyncio.gather(client_task, interactive_task)

if __name__ == "__main__":
    wrapper = InteractiveClient()
    asyncio.run(wrapper.main())
