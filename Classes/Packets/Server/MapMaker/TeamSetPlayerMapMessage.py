from Classes.Packets.PiranhaMessage import PiranhaMessage

class TeamSetPlayerMapMessage(PiranhaMessage):
    def __init__(self, messageData):
        super().__init__(messageData)
        self.messageVersion = 0

    def decode(self):
        self.fields = {}
        # ReadVLong in C# solitamente legge High e Low
        # Usiamo il metodo della tua classe ByteStream per i Long
        self.fields["MapIdHigh"] = self.readVInt()
        self.fields["MapIdLow"] = self.readVInt()
        
        # Salviamo l'ID completo nel dizionario fields
        self.fields["MapId"] = self.fields["MapIdLow"]
        return self.fields

    def execute(self, player, fields):
        # Logica per impostare la mappa nella stanza del team
        if player.TeamId > 0:
            # Qui dovresti avere una logica che recupera l'oggetto Team
            # e imposta la mappa scelta dal giocatore come mappa attiva
            print(f"[MapMaker] Player [0, 1] ha selezionato la mappa ID {fields['MapId']} per il Team.")
            
            # Esempio ipotetico di aggiornamento del team:
            # team = TeamManager.get_team(player.TeamId)
            # if team:
            #    team.set_custom_map(fields["MapId"])
        else:
            print("[MapMaker] Il giocatore non è in un team, impossibile impostare la mappa.")

    def getMessageType(self):
        return 12110

    def getMessageVersion(self):
        return self.messageVersion