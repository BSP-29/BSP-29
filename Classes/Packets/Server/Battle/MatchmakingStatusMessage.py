from Classes.Packets.PiranhaMessage import PiranhaMessage


class MatchmakingStatusMessage(PiranhaMessage):
    """v29 matchmaking status payload."""

    def __init__(self, messageData):
        super().__init__(messageData)
        self.messageVersion = 4

    def encode(self, fields, player=None):
        self.writeInt(30)
        self.writeLong(0, 0)
        self.writeInt(3)
        self.writeInt(2)
        self.writeInt(1)


    def decode(self):
        return {}

    def execute(self, *args, **kwargs):
        pass

    def getMessageType(self):
        return 20405

    def getMessageVersion(self):
        return self.messageVersion
