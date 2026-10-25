from Classes.Packets.PiranhaMessage import PiranhaMessage
from Classes.Messaging import Messaging

class AskJoinableAlliancesMessage(PiranhaMessage):
    def __init__(self, messageData):
        super().__init__(messageData)
        self.id = 14303
        self.messageVersion = 0

    def decode(self):
        pass

    def execute(message, calling_instance, fields, cryptoInit):

        if fields is None:
            fields = {}
        fields["Socket"] = calling_instance.client
        Messaging.sendMessage(24304, fields, cryptoInit, calling_instance.player)

    def getMessageType(self):
        return self.id

    def getMessageVersion(self):
        return self.messageVersion