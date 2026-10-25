from Classes.Packets.PiranhaMessage import PiranhaMessage

class GoHomeFromMapEditorMessage(PiranhaMessage):
    def __init__(self, messageData):
        super().__init__(messageData)
        self.messageVersion = 0

    def decode(self):
        # Messaggio vuoto nel protocollo originale, nessun dato da leggere
        return {}

    def execute(self, player, fields):
        # Logica per gestire il ritorno alla Home
        # Spesso viene usato per inviare nuovamente l'OwnHomeDataMessage (24101)
        # per aggiornare eventuali cambiamenti visivi.
        print(f"[MapMaker] Player [0, 1] è uscito dal Map Editor.")
        pass

    def getMessageType(self):
        return 12108

    def getMessageVersion(self):
        return self.messageVersion