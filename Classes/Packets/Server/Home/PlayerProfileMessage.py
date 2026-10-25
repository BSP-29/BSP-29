from Classes.Instances.Classes.Player import Player  # Importiamo la classe Player completa
from Classes.Packets.PiranhaMessage import PiranhaMessage

class PlayerProfileMessage(PiranhaMessage):
    def __init__(self, messageData):
        super().__init__(messageData)
        self.messageVersion = 0
        self.id = 24113

    def encode(self, fields, player):
        # Usiamo il LowID richiesto dal client
        requestedLowID = fields.get("PlayerLowID", player.LowID)
        
        # Istanziamo il player target correttamente: questo caricherà 
        # automaticamente sia DynamicDB che AllianceDatabase[span_1](start_span)[span_1](end_span)
        target = Player(requestedLowID)
        
        self.writeVInt(fields.get("PlayerHighID", 0))
        self.writeVInt(requestedLowID)
        self.writeVInt(0)

        # Brawlers (Lista vuota o gestita dal target.UnlockedBrawlers se implementato)
        self.writeVInt(0) 

        # Statistiche Profilo
        self.writeVInt(15)
        self.writeVInt(1); self.writeVInt(target.ThreeVThree)
        self.writeVInt(2); self.writeVInt(target.Experience)
        self.writeVInt(3); self.writeVInt(target.Trophies)
        self.writeVInt(4); self.writeVInt(target.HighestTrophies)
        self.writeVInt(5); self.writeVInt(45) # Brawlers Unlocked
        self.writeVInt(7); self.writeVInt(28000000 + target.Thumbnail)
        self.writeVInt(8); self.writeVInt(target.SoloWins)
        self.writeVInt(9); self.writeVInt(target.RoboRumble)
        self.writeVInt(10); self.writeVInt(target.Kaiju)
        self.writeVInt(11); self.writeVInt(target.DuoWins)
        self.writeVInt(12); self.writeVInt(target.Boss)
        self.writeVInt(13); self.writeVInt(target.PowerPlayPoints)
        self.writeVInt(14); self.writeVInt(target.PLLP)
        self.writeVInt(15); self.writeVInt(target.ChallengeWins)
        self.writeVInt(16); self.writeVInt(target.Kaiju)

        # Nome e Dati Base
        self.writeString(target.Name)
        self.writeVInt(target.Experience)
        self.writeVInt(28000000 + target.Thumbnail)
        self.writeVInt(43000000 + target.Namecolor)
        self.writeVInt(4600001)

        # Club (Usa gli attributi caricati automaticamente da _load_alliance_data)[span_2](start_span)[span_2](end_span)
        if target.ClubLowID != 0:
            self.writeBoolean(True)
            self.writeInt(0)
            self.writeInt(target.ClubLowID)
            self.writeString(target.ClubName)
            self.writeVInt(8)
            self.writeVInt(target.ClubIcon)
            self.writeVInt(target.ClubType)
            self.writeVInt(target.ClubMemberCount)
            self.writeVInt(target.ClubTrophies)
            self.writeVInt(target.ClubMinimumJoinTrophies)
            self.writeVInt(0)
            self.writeString(target.Region)
            self.writeVInt(0)
            self.writeVInt(0)
            self.writeVInt(25)
            self.writeVInt(target.ClubRole)
        else:
            self.writeBoolean(False)
            self.writeVInt(0)

    def decode(self): pass
    def execute(self, calling_instance, fields, cryptoInit): pass
    def getMessageType(self): return self.id
    def getMessageVersion(self): return self.messageVersion