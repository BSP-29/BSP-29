from Classes.Packets.PiranhaMessage import PiranhaMessage
from Classes.DB.AllianceDB import AllianceDatabase
import json


class AllianceMemberEntryMessage(PiranhaMessage):

    def __init__(self, messageData):
        super().__init__(messageData)
        self.id = 24308
        self.messageVersion = 0

    def encode(self):
        # Ottieni l'alliance del player dal database
        alliance = player.alliance_db.getPlayerAlliance(player.LowID)
        
        if alliance is None:
            self.writeInt(0)  # Club HighID
            self.writeInt(0)  # Club LowID
            return
        
        clubid = alliance["id"]
        
        self.writeInt(0)  # Club HighID
        self.writeInt(clubid)  # Club LowID
        
        self.writeInt(0)
        self.writeInt(player.LowID)
        self.writeString(player.Name)  # Player name
        self.writeVInt(player.Experience)
        self.writeVInt(28000000 + player.Thumbnail)  # Profile icon
        self.writeVInt(43000000 + player.Namecolor)  # Name color
        self.writeVInt(-1)  # ChromaName

    def decode(self):
        pass

    def getMessageType(self):
        return self.id

    def getMessageVersion(self):
        return self.messageVersion