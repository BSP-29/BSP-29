import json
from Classes.Packets.PiranhaMessage import PiranhaMessage

class AllianceLeaveOkMessage(PiranhaMessage):
    def __init__(self, messageData):
        super().__init__(messageData)
        self.id = 24333
        self.messageVersion = 0

    def encode(self):
        self.writeVint(80) # Event type

    def getMessageType(self):
        return self.id

    def getMessageVersion(self):
        return self.messageVersion