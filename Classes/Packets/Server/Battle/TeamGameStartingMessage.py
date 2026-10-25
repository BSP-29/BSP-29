from Classes.Packets.PiranhaMessage import PiranhaMessage


class TeamGameStartingMessage(PiranhaMessage):
    """24130, sent to every team member just before the loading screen."""

    def __init__(self, messageData):
        super().__init__(messageData)
        self.messageVersion = 9   # <-- CORRETTO (era 0)

    def encode(self, fields, player=None):
        # offset 132: VInt
        self.writeVInt(0)
        # offset 136: VInt
        self.writeVInt(0)
        # offset 144: DataReference (high, low)
        self.writeDataReference(15, int(fields.get("LocationID", 0)))

    def decode(self):
        return {}

    def execute(self, *args, **kwargs):
        pass

    def getMessageType(self):
        return 24130

    def getMessageVersion(self):
        return self.messageVersion