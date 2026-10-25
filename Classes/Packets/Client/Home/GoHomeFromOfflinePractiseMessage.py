from Classes.Messaging import Messaging
from Classes.Packets.PiranhaMessage import PiranhaMessage


class GoHomeFromOfflinePractiseMessage(PiranhaMessage):
    def __init__(self, messageData):
        super().__init__(messageData)
        self.messageVersion = 0

    def encode(self, fields):
        pass

    def decode(self):
        fields = {}
        self.readBoolean()
        return fields

    def execute(message, calling_instance, fields, cryptoInit):
        fields["Socket"] = calling_instance.client
        player = calling_instance.player

        from Classes.BattleServer import remove_battle_session
        completed_room_id = remove_battle_session(player)
        
        # === AGGIORNA I TROFEI TOTALI DAL DB PRIMA DI INVIARE LA HOME ===
        player.update_total_trophies()
        
        # === CARICA I TROFEI DEL BRAWLER SELEZIONATO DAL DB ===
        player.load_brawler_trophies()
        
        print(f"[GoHome] Updated trophies - Total: {player.Trophies}, Brawler: {player.BrawlerTrophies}, Rewarded: {player.TrophiesRewarded}")
        
        # Invia OwnHomeDataMessage con i dati aggiornati
        Messaging.sendMessage(24101, fields, cryptoInit, player)
        if completed_room_id:
            from Classes.TeamMatchmaking import broadcast_team
            broadcast_team(completed_room_id)

    def getMessageType(self):
        return 14109

    def getMessageVersion(self):
        return self.messageVersion
