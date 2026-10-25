from Classes.Packets.PiranhaMessage import PiranhaMessage


class MatchmakingCancelledMessage(PiranhaMessage):
    def __init__(self, messageData):
        super().__init__(messageData)
        self.messageVersion = 0

    def encode(self, fields, player=None):
        pass

    def decode(self):
        return {}

    def execute(self, *args, **kwargs):
        pass

    def getMessageType(self):
        return 20406

    def getMessageVersion(self):
        return self.messageVersion
