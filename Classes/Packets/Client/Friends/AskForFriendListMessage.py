from Classes.Messaging import Messaging
from Classes.Packets.PiranhaMessage import PiranhaMessage
from Classes.DB.DynamicDB import DynamicDB as DB

class AskForFriendListMessage(PiranhaMessage):
    def __init__(self, messageData):
        super().__init__(messageData)
        self.id = 10504
        self.messageVersion = 0

    def decode(self):
        return {}

    def execute(self, calling_instance, fields, cryptoInit):
        player = calling_instance.player
        
        # === RICARICA FORZATAMENTE I DATI DEL PLAYER DAL DB ===
        player.load_from_db()
        
        # 1. Invia la lista amici del player
        Messaging.sendMessage(20105, {"Socket": calling_instance.client}, cryptoInit, player)
        
        # 2. Invia lo stato online per ogni amico
        db_player = DB(player_id=str(player.LowID))
        friends_list = db_player.get_friends_list()
        
        for friend in friends_list:
            if friend.get('state') == 4:  # Solo amici accettati
                status_fields = {
                    "TargetLowID": friend.get('id', 0),
                    "Status": 0,
                    "RoomID": 0,
                    "IsOnline": False,
                    "LastSeen": 0
                }
                Messaging.sendMessage(24555, status_fields, cryptoInit, player)
        
        print(f"[AskForFriendList] Sent friend list to {player.Name}")

    def getMessageVersion(self):
        return self.messageVersion

    def getMessageType(self):
        return self.id
