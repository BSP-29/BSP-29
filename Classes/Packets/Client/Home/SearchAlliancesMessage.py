from Classes.Packets.PiranhaMessage import PiranhaMessage
from Classes.Messaging import Messaging
from Classes.Instances.Classes.Player import Player


class SearchAlliancesMessage(PiranhaMessage):

    def __init__(self, messageData):
        super().__init__(messageData)

        self.messageVersion = 0
        self.id = 14301

    def decode(self):
        self.RequestedName = self.readString()
        
    def execute(self, message, fields, cryptoInit):

        fields = fields or {}
        fields["SearchName"] = self.RequestedName
      
        client = getattr(cryptoInit, "client", None)

        if client is None:
            print("[ERROR] client not found (dispatcher missing player/calling_instance)")
            client = self.player.client

        Messaging.sendMessage(
            24310,
            fields,
            cryptoInit,
            self.player.client
        )

    def getMessageVersion(self):
        return self.messageVersion

    def getMessageType(self):
        return self.id