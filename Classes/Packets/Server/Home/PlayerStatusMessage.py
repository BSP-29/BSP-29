from Classes.Packets.PiranhaMessage import PiranhaMessage


class PlayerStatusMessage(PiranhaMessage):
    """v29 PlayerStatusMessage (14366)."""

    def __init__(self, messageData):
        super().__init__(messageData)
        self.id = 14366
        self.messageVersion = 0

    def encode(self, fields, player=None):
        self.writeVInt(int(fields.get("Status", 0) or 0))

    def decode(self):
        fields = {}
        fields["Status"] = self.readVInt()
        super().decode(fields)
        return fields

    def execute(self, calling_instance, fields, cryptoInit):
        pass

    def getMessageType(self):
        return 14366

    def getMessageVersion(self):
        return self.messageVersion
