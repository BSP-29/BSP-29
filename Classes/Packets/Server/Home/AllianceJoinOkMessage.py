import json
from Classes.Packets.PiranhaMessage import PiranhaMessage

class AllianceJoinOkMessage(PiranhaMessage):
    def __init__(self, messageData):
        super().__init__(messageData)
        self.id = 24333
        self.player = player

    def encode(self):
        self.writeVInt(40) # Event type

    def getMessageType(self):
        return self.id

    def getMessageVersion(self):
        return self.messageVersion