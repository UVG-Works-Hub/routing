import tkinter as tk
from tkinter import scrolledtext, messagebox
import asyncio
import yaml
from NetworkClient import NetworkClient

class InteractiveClientGUI:
    def __init__(self, master):
        self.master = master
        master.title("Interactive XMPP Client")
        master.geometry("600x600")

        self.client = None
        self.config = None
        self.last_log = 0

        # Config file input
        tk.Label(master, text="Config File Path:").pack()
        self.config_path = tk.Entry(master, width=50)
        self.config_path.pack()
        tk.Button(master, text="Load Config", command=self.load_config).pack()

        # Log display area
        self.log_area = scrolledtext.ScrolledText(master, wrap=tk.WORD, width=70, height=20)
        self.log_area.pack(padx=10, pady=10)

        # Message sending area
        tk.Label(master, text="Recipient JID:").pack()
        self.recipient_jid = tk.Entry(master, width=50)
        self.recipient_jid.pack()

        tk.Label(master, text="Message Type:").pack()
        self.message_type = tk.Entry(master, width=50)
        self.message_type.pack()

        tk.Label(master, text="Message:").pack()
        self.message_entry = tk.Entry(master, width=50)
        self.message_entry.pack()

        tk.Button(master, text="Send Message", command=self.send_message).pack(pady=10)

    async def get_logs(self):
        while True:
            if self.client:
                await asyncio.sleep(2)
                logs = self.client.send_log()
                for index, log in enumerate(logs):
                    if index >= self.last_log:
                        self.log(log)
                        self.last_log += 1

    def load_config(self):
        config_file = self.config_path.get()
        try:
            with open(config_file, 'r') as file:
                self.config = yaml.safe_load(file)
            self.initialize_client()
            self.log("Config loaded successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load config: {str(e)}")

    def initialize_client(self):
        self.client = NetworkClient(
            jid=self.config["jid"],
            password=self.config["password"],
            neighbors=self.config["neighbors"],
            costs=self.config["costs"],
            mode=self.config["mode"]
        )
        asyncio.create_task(self.run_client())
        asyncio.create_task(self.get_logs())

    async def run_client(self):
        try:
            await self.client.connect_and_process()
        except Exception as e:
            self.log(f"Error in client processing: {str(e)}")

    def send_message(self):
        if not self.client:
            messagebox.showerror("Error", "Client not initialized. Please load configuration first.")
            return

        to_jid = self.recipient_jid.get()
        messageType = self.message_type.get()
        payload = self.message_entry.get()
        asyncio.create_task(self.client.send_message_to(to_jid, {
            "type": messageType or "message",
            "from": self.client.boundjid.full,
            "to": to_jid,
            "payload": payload,
            "hops": 0,
            "headers": []
        }))
        self.log(f"Message sent to {to_jid}")

    def log(self, message):
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)

def main():
    root = tk.Tk()
    app = InteractiveClientGUI(root)
    
    async def run_tk(root, interval=0.05):
        try:
            while True:
                root.update()
                await asyncio.sleep(interval)
        except tk.TclError as e:
            if "application has been destroyed" not in str(e):
                raise

    asyncio.run(run_tk(root))

if __name__ == "__main__":
    main()