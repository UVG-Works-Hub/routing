import sys
if sys.platform == 'win32':
    import asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import slixmpp

jabberid = "cha21881@alumchat.lol"
password = "admin"
receiver = "cha21881siete@alumchat.lol"
message  = "Hello, this is a message sent from Python!"

class SendMsgBot(slixmpp.ClientXMPP):
    def __init__(self, jid, password, recipient, message):
        slixmpp.ClientXMPP.__init__(self, jid, password)
        self.recipient = recipient
        self.msg = message

        self.add_event_handler("session_start", self.start)
        self.add_event_handler("message", self.message)

    async def start(self, event):
        self.send_presence()
        await self.get_roster()

        print(f"Sending message to {self.recipient}")

        self.send_message(mto=self.recipient,
                          mbody=self.msg,
                          mtype='chat')

    def message(self, msg):
        if msg['type'] in ('chat', 'normal'):
            print(f"Received message: {msg['body']}")

async def main():
    jid = jabberid
    xmpp = SendMsgBot(jid, password, receiver, message)
    xmpp.connect((jid.split('@')[1], 7070), disable_starttls=True)
    await xmpp.disconnected

if __name__ == "__main__":
    asyncio.run(main())
