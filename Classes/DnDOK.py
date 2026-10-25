from Classes.Packets.PiranhaMessage import PiranhaMessage


class DnDOK(PiranhaMessage):

    def __init__(self, messageData):
        super().__init__(messageData)
        self.id = 24111
        self.messageVersion = 0

    def encode(self, fields, player=None):
        self.writeVInt(213)
        self.writeVInt(player.DnDState)
        self.writeVInt(0)
        self.writeVInt(0)
        self.writeVInt(0)
        self.writeVInt(0)
        self.writeVInt(0)
    
    def getMessageType(self):
        return self.id

    def getMessageVersion(self):
        return self.messageVersion