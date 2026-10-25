from Packets.Messages.Server.Alliance.AllianceDataMessage import AllianceDataMessage
from Classes.Packets.PiranhaMessage import PiranhaMessage


class AskForAllianceDataMessage(PiranhaMessage):
    def __init__(self, messageData):
        super().__init__(messageData)
        self.messageVersion = 0

    def decode(self):
        self.clubHighID = self.read_int()
        self.clubLowID = self.read_int()

    def execute(self):
        Messaging.sendMessage(24301, fields, cryptoInit, calling_instance.player)