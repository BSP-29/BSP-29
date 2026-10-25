from Classes.Packets.PiranhaMessage import PiranhaMessage


class StartLoadingMessage(PiranhaMessage):
    def __init__(self, messageData):
        super().__init__(messageData)
        self.messageVersion = 4   # <-- CORRETTO: il client si aspetta 4

    def encode(self, fields, player=None):
        players = fields.get("Players", [])

        # Header
        self.writeInt(len(players))                      # offset 132
        self.writeInt(int(fields.get("OwnIndex", 0)))    # offset 136
        self.writeInt(int(fields.get("TeamIndex", 0)))   # offset 140
        self.writeInt(len(players))                      # numero di player

        for entry in players:
            self.writeInt(0xFFFFFFFF)  # AccountID (empty)
            self.writeVInt(0)          # PlayerIndex
            self.writeVInt(0)          # TeamIndex
            self.writeVInt(0)
            self.writeInt(0)
            self.writeDataReference(16, 115)   # Brawler
            self.writeDataReference(29, 216)   # Skin
            self.writeBoolean(False)
            self.writeString("BSP|Official")
            self.writeVInt(100)        # Level
            self.writeVInt(28000000)   # Thumbnail
            self.writeVInt(43000000)   # NameColor
            self.writeVInt(0)          # ChromaticName

        # Liste vuote
        self.writeInt(0)  # skins
        self.writeInt(0)  # star powers

        # Campi finali
        self.writeInt(0)                                 # offset 144 (random seed?)
        self.writeVInt(int(fields.get("GameMode", 1)))   # offset 148
        self.writeVInt(1)                                # offset 152
        self.writeVInt(1)                                # offset 156
        self.writeBoolean(True)                          # offset 160
        self.writeVInt(int(fields.get("SpectateMode", 0)))  # offset 164
        self.writeVInt(0)                                # offset 168
        self.writeDataReference(15, int(fields.get("LocationID", 0)))  # offset 176
        self.writeBoolean(False)                         # offset 172
        self.writeBoolean(False)                         # offset 173

    def decode(self):
        return {}

    def execute(self, *args, **kwargs):
        pass

    def getMessageType(self):
        return 20559

    def getMessageVersion(self):
        return self.messageVersion