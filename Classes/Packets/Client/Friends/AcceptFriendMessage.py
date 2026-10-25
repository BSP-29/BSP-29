from Classes.Messaging import Messaging
from Classes.Packets.PiranhaMessage import PiranhaMessage
from Classes.DB.DynamicDB import DynamicDB as DB
from Classes.ClientsManager import ClientsManager

class AcceptFriendMessage(PiranhaMessage):
    def __init__(self, messageData):
        super().__init__(messageData)
        self.id = 10501
        self.messageVersion = 0

    def decode(self):
        fields = {}
        fields["HighID"] = self.readInt()
        fields["LowID"] = self.readInt()
        return fields

    def execute(self, calling_instance, fields, cryptoInit):
        player = calling_instance.player
        try:
            target_low_id = int(fields.get("LowID", 0) or 0)
        except (TypeError, ValueError):
            target_low_id = 0

        if target_low_id <= 0 or target_low_id == int(player.LowID):
            print("[AcceptFriend] Invalid target ID")
            return

        db_target = DB(player_id=str(target_low_id))
        if not db_target._load_raw():
            print(f"[AcceptFriend] Target {target_low_id} does not exist")
            return

        print(f"[AcceptFriend] {player.Name} accepting friend from {target_low_id}")

        # === 1. AGGIORNA IL PLAYER ===
        db_player = DB(player_id=str(player.LowID))
        friends = db_player.get_friends_list() or []
        
        def accept_relation(friend_list, friend_id):
            result = []
            found = False
            for friend in friend_list:
                if not isinstance(friend, dict):
                    continue
                try:
                    current_id = int(friend.get("id", -1))
                except (TypeError, ValueError):
                    current_id = -1
                if current_id == friend_id:
                    if not found:
                        result.append({"id": friend_id, "state": 4})
                        found = True
                else:
                    result.append(friend)
            if not found:
                result.append({"id": friend_id, "state": 4})
            return result

        friends = accept_relation(friends, target_low_id)
        db_player.set_friends_list(friends)

        # === 2. AGGIORNA IL TARGET ===
        target_friends = db_target.get_friends_list() or []
        
        target_friends = accept_relation(target_friends, int(player.LowID))
        db_target.set_friends_list(target_friends)

        print(f"🤝 {player.Name} e {target_low_id} sono ora amici!")

        Messaging.sendMessage(20105, {"Socket": calling_instance.client}, cryptoInit, player)

        target_client = ClientsManager.GetAll().get(target_low_id, {})
        target_session = target_client.get("Session")
        if target_session is not None:
            target_player = getattr(target_session, "player", None)
            target_crypto = getattr(target_session, "cryptoInit", None)
            target_socket = getattr(target_session, "client", None)
            if target_player is not None and target_crypto is not None and target_socket is not None:
                Messaging.sendMessage(
                    20105,
                    {"Socket": target_socket},
                    target_crypto,
                    target_player,
                )

    def getMessageVersion(self):
        return self.messageVersion

    def getMessageType(self):
        return self.id
