from Classes.Logic.PlayAgainStatusMessage import PlayAgainStatusMessage
from Classes.Messaging import Messaging
from Classes.Packets.PiranhaMessage import PiranhaMessage


class PlayAgainMessage(PiranhaMessage):
    def __init__(self, messageData, player=None, client=None):
        super().__init__(messageData)
        self.messageVersion = 0
        self.player = player
        self.client = client

    def decode(self):
        pass

    def execute(self, calling_instance, fields, cryptoInit):
        if fields is None:
            fields = {}
        
        fields["Socket"] = calling_instance.client
        Messaging.sendMessage(24777, fields, cryptoInit, self.player)

    def getMessageType(self):
        return 14177

    def getMessageVersion(self):
        return self.messageVersion