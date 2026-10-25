from Classes.Packets.PiranhaMessage import PiranhaMessage


class ServerErrorMessage(PiranhaMessage):
    def __init__(self, messageData):
        super().__init__(messageData)
        self.messageVersion = 0

    def encode(self, fields, player=None):
        # ErrorCode: codice intero custom (es. 16 = VIP required)
        # Message: testo da mostrare (il client/mod lo leggerà)
        self.writeVInt(fields.get("ErrorCode", 0))
        self.writeString(fields.get("Message", ""))

    def decode(self):
        fields = {}
        fields["ErrorCode"] = self.readVInt()
        fields["Message"] = self.readString()
        super().decode(fields)
        return fields

    def execute(message, calling_instance, fields):
        # lato server non fa nulla
        pass

    def getMessageType(self):
        return 24115  # ServerErrorMessage

    def getMessageVersion(self):
        return self.messageVersion
