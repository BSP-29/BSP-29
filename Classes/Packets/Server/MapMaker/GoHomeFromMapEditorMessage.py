from Classes.Packets.PiranhaMessage import PiranhaMessage

class GoHomeFromMapEditorMessage(PiranhaMessage):
    def __init__(self, messageData):
        super().__init__(messageData)
        self.messageVersion = 0

    def decode(self):
        return {}

    def execute(self, player, fields):
        print(f"[MapMaker] Player [0, 1] è uscito dal Map Editor.")
        pass

    def getMessageType(self):
        return 12108

    def getMessageVersion(self):
        return self.messageVersion