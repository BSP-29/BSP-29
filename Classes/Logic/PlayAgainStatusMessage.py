from Classes.Packets.PiranhaMessage import PiranhaMessage

class PlayAgainStatusMessage(PiranhaMessage):
    def __init__(self, messageData=b''):
        # Passiamo solo messageData alla classe base
        super().__init__(messageData)
        self.id = 24777
        self.messageVersion = 0

    def encode(self, player):
        # Numero di entry (giocatori che hanno risposto)
        self.writeVInt(3) 

        # Giocatore 1 (Tu)
        self.writeLong(0, 3)
        self.writeVInt(0) # Stato: 1 = Accettato

        # Giocatore 2 (Bot fittizio)
        self.writeLong(0, 1)
        self.writeVInt(0) 

        # Giocatore 3 (Bot fittizio)
        self.writeLong(0, 2)
        self.writeVInt(0)

    def getMessageType(self):
        return 24777