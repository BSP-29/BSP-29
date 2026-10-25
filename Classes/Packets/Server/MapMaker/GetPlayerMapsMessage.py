from Classes.Packets.PiranhaMessage import PiranhaMessage
from Classes.Packets.Server.MapMaker.PlayerMapsMessage import PlayerMapsMessage

class GetPlayerMapsMessage(PiranhaMessage):
    def __init__(self, messageData):
        super().__init__(messageData)
        self.messageVersion = 0

    def decode(self):
        # Il corpo del messaggio è vuoto nel protocollo originale
        return {}

    def execute(self, player, fields):
        # Quando il client richiede le mappe, noi rispondiamo con la lista dal DB
        print(f"[MapMaker] Il player {player.ID} ha richiesto la lista mappe.")
        
        # Invio del messaggio 22102 che abbiamo creato precedentemente
        response = PlayerMapsMessage(b'')
        player.sendNetMessage(response)

    def getMessageType(self):
        return 12102

    def getMessageVersion(self):
        return self.messageVersion