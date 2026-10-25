from Classes.Packets.PiranhaMessage import PiranhaMessage


class UpdatePlayerMapResponseMessage(PiranhaMessage):
    def __init__(self, messageData):
        super().__init__(messageData)
        # writeHeader always reads messageVersion, so a class that never sets it
        # raised AttributeError after the crypto nonce had already been consumed.
        self.messageVersion = 0
        self.mapId = 0
        self.errorCode = 0

    def encode(self, fields, player=None):
        # Values arrive through fields: Messaging builds a fresh instance from
        # the factory, so instance attributes set by the caller are not kept.
        self.writeVInt(int(fields.get("errorCode", 0) or 0))
        # LogicLong (High + Low)
        self.writeVInt(0)
        self.writeVInt(int(fields.get("mapId", 0) or 0))

    def getMessageType(self):
        return 22103

    def getMessageVersion(self):
        return self.messageVersion