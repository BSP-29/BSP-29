import json
import os
from Classes.Messaging import Messaging
from Classes.Packets.PiranhaMessage import PiranhaMessage
from Classes.DB.DynamicDB import DynamicDB as DB

class RemoveFriendMessage(PiranhaMessage):
    def __init__(self, messageData):
        super().__init__(messageData)
        self.id = 10506
        self.messageVersion = 0

    def decode(self):
        fields = {}
        fields["HighID"] = self.readInt()
        fields["LowID"] = self.readInt()
        return fields

    def execute(self, calling_instance, fields, cryptoInit):
        player = calling_instance.player
        target_low_id = fields.get("LowID", 0)

        if target_low_id == 0:
            print("[RemoveFriend] Invalid target ID")
            return

        print(f"[RemoveFriend] {player.Name} removing friend {target_low_id}")

        # === 1. RIMUOVI DAL PLAYER ===
        db_player = DB(player_id=str(player.LowID))
        friends = db_player.get_friends_list()
        new_friends = [f for f in friends if f.get('id') != target_low_id]
        
        if len(new_friends) != len(friends):
            db_player.set_friends_list(new_friends)
            print(f"[RemoveFriend] Removed {target_low_id} from {player.Name}")

        # === 2. RIMUOVI DAL TARGET ===
        db_target = DB(player_id=str(target_low_id))
        target_friends = db_target.get_friends_list()
        new_target_friends = [f for f in target_friends if f.get('id') != player.LowID]
        
        if len(new_target_friends) != len(target_friends):
            db_target.set_friends_list(new_target_friends)
            print(f"[RemoveFriend] Removed {player.LowID} from {target_low_id}")

        print(f"💔 Amicizia rimossa tra {player.Name} e {target_low_id}")

        # === 3. RICARICA I DATI DEL PLAYER DAL DB ===
        player.load_from_db()
        
        # === 4. INVIA LA LISTA AGGIORNATA ===
        Messaging.sendMessage(20105, {"Socket": calling_instance.client}, cryptoInit, player)

    def getMessageVersion(self):
        return self.messageVersion

    def getMessageType(self):
        return self.id