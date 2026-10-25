from Classes.Packets.PiranhaMessage import PiranhaMessage

class FriendListUpdateMessage(PiranhaMessage):
    def __init__(self, messageData):
        super().__init__(messageData)
        self.messageVersion = 0

    def encode(self, fields, player):
        # Prendiamo i dati del player da aggiornare dai fields
        target_data = fields.get("TargetData")
        target_state = fields.get("TargetState", 0)
        
        # Indica quanti amici stiamo aggiornando (solitamente 1)
        self.writeVInt(1) 

        # Identificativi
        self.writeLong(0, target_data.get("LowID", 1))

        # Stringhe Social (vuote)
        for _ in range(6):
            self.writeString("")

        self.writeVInt(target_data.get("Trophies", 0)) # Trofei aggiornati
        self.writeVInt(target_state) # Nuovo stato (es. 4 se ha accettato)
        
        self.writeVInt(0)
        self.writeVInt(0)
        self.writeVInt(0)

        self.writeBoolean(False) # In match?

        self.writeString("") # Nome Clan
        self.writeVInt(0)    # Ruolo Clan

        self.writeBoolean(True) # Ha dati profilo?

        # Dati estetici aggiornati
        self.writeString(target_data.get("Name", "Player"))
        self.writeVInt(100) # Exp Level
        self.writeVInt(28000000 + target_data.get("Thumbnail", 0))
        self.writeVInt(43000000 + target_data.get("Namecolor", 0))

    def getMessageVersion(self):
        return self.messageVersion

    def getMessageType(self):
        return 20106