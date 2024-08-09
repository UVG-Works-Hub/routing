import slixmpp
import asyncio

jabberid = "don21610@alumchat.lol"
password = "admin123"
receiver = "gar21285@alumchat.lol"
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

        self.send_message(mto=self.recipient,
                          mbody=self.msg,
                          mtype='chat')

        self.disconnect()

    def message(self, msg):
        if msg['type'] in ('chat', 'normal'):
            print(f"Received message: {msg['body']}")

def main():
    jid = jabberid
    xmpp = SendMsgBot(jid, password, receiver, message)
    xmpp.connect((jid.split('@')[1], 7070), disable_starttls=True)
    xmpp.process(forever=True)

if __name__ == "__main__":
    main()