import json
from Classes.Packets.PiranhaMessage import PiranhaMessage


class JoinableAllianceListMessage(PiranhaMessage):

    def __init__(self, messageData):
        super().__init__(messageData)
        self.messageVersion = 0
        self.id = 24304

    def encode(self, fields, player=None):
        # Ottieni tutte le alliance dal database SQLite del player
        all_alliances = player.alliance_db.getAllAlliances()
        
        # Filtra le alliance joinable (esempio: member_count < 50 e trophies >= 50)
        joinable_alliances = [
            a for a in all_alliances 
            if a["member_count"] < 50 and a["trophies"] >= 50
        ]
        
        AllianceCount = len(joinable_alliances)
        self.writeVInt(AllianceCount)

        for alliance in joinable_alliances:
            clubid = alliance["id"]
            
            self.writeInt(0)
            self.writeInt(clubid)
            self.writeString(alliance["name"])

            self.writeVInt(8)
            self.writeVInt(alliance["badge_id"])

            self.writeVInt(alliance["type"])

            self.writeVInt(alliance["member_count"])

            self.writeVInt(alliance["trophies"])
            self.writeVInt(alliance["trophies_needed"])
            self.writeVInt(0)

            self.writeString(alliance["region"])
            self.writeVInt(alliance["member_count"])
            self.writeVInt(alliance["friendly_family"])

    def decode(self):
        pass

    def getMessageType(self):
        return self.id

    def getMessageVersion(self):
        return self.messageVersion