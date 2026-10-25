from Classes.Packets.PiranhaMessage import PiranhaMessage

class FriendOnlineStatusEntryMessage(PiranhaMessage):
    def __init__(self, messageData):
        super().__init__(messageData)
        self.messageVersion = 0

    def encode(self, fields, player):
        # Prendiamo i dati passati nel dizionario fields
        target_low_id = fields.get("TargetLowID")
        status = fields.get("Status")   # 0: Offline, 1: Online/Lobby, 2: In Battle
        room_id = fields.get("RoomID", 0)

        # Identificativi (HighID e LowID)
        self.writeLong(0, target_low_id)
        
        # Ripetizione ID (standard v29)
        self.writeBoolean(True)
        self.writeLong(0, target_low_id)
        
        # Stato effettivo
        self.writeVInt(status) 
        
        # Se status è 0 (offline), questo valore dovrebbe essere 1 per confermare l'uscita
        if status == 0:
            self.writeVInt(1)
        else:
            self.writeVInt(0)

        # Se il giocatore è in una stanza (Lobby), mostra il tasto "Partecipa"
        if room_id > 0:
            self.writeBoolean(True) # Is in room
        else:
            self.writeBoolean(False)
            
        # Ulteriore flag (solitamente False)
        self.writeBoolean(False)

    def getMessageType(self):
        return 24555

    def getMessageVersion(self):
        return self.messageVersion