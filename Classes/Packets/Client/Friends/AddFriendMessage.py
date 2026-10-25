from Classes.Messaging import Messaging
from Classes.Packets.PiranhaMessage import PiranhaMessage
from Classes.DB.DynamicDB import DynamicDB as DB
from Classes.ClientsManager import ClientsManager

class AddFriendMessage(PiranhaMessage):
    def __init__(self, messageData):
        super().__init__(messageData)
        self.id = 10502
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
            sender_low_id = int(player.LowID)
        except (TypeError, ValueError):
            target_low_id = 0
            sender_low_id = int(getattr(player, "LowID", 0) or 0)

        if target_low_id <= 0 or target_low_id == sender_low_id:
            print("[AddFriend] Invalid target ID")
            return

        db_target = DB(player_id=str(target_low_id))
        if not db_target._load_raw():
            print(f"[AddFriend] Target {target_low_id} does not exist")
            return

        print(f"[AddFriend] {player.Name} (ID: {player.LowID}) sending friend request to {target_low_id}")

        # The v28 client expects state 2 on the sender and state 3 on the
        # recipient. State 4 means both sides accepted the request.
        db_sender = DB(player_id=str(player.LowID))
        sender_friends = db_sender.get_friends_list() or []
        target_friends = db_target.get_friends_list()

        def find_relation(friends, friend_id):
            for friend in friends:
                if not isinstance(friend, dict):
                    continue
                try:
                    if int(friend.get("id", -1)) == friend_id:
                        return friend
                except (TypeError, ValueError):
                    continue
            return None

        sender_relation = find_relation(sender_friends, target_low_id)
        target_relation = find_relation(target_friends, sender_low_id)
        try:
            sender_relation_state = int(sender_relation.get("state", 0) or 0) if sender_relation else 0
        except (TypeError, ValueError):
            sender_relation_state = 0
        try:
            target_relation_state = int(target_relation.get("state", 0) or 0) if target_relation else 0
        except (TypeError, ValueError):
            target_relation_state = 0
        already_friends = sender_relation_state == 4 or target_relation_state == 4
        reciprocal_request = (
            sender_relation_state == 3 or target_relation_state == 2
        )
        sender_state = 4 if already_friends or reciprocal_request else 2
        target_state = 4 if already_friends or reciprocal_request else 3

        def upsert_relation(friends, friend_id, state):
            result = []
            found = False
            for friend in friends:
                if not isinstance(friend, dict):
                    continue
                try:
                    current_id = int(friend.get("id", -1))
                except (TypeError, ValueError):
                    current_id = -1
                if current_id == friend_id:
                    if not found:
                        result.append({"id": friend_id, "state": state})
                        found = True
                else:
                    result.append(friend)
            if not found:
                result.append({"id": friend_id, "state": state})
            return result

        sender_friends = upsert_relation(sender_friends, target_low_id, sender_state)
        target_friends = upsert_relation(target_friends, sender_low_id, target_state)
        db_sender.set_friends_list(sender_friends)
        db_target.set_friends_list(target_friends)

        print(f"[AddFriend] {sender_low_id} -> {target_low_id}, states {sender_state}/{target_state}")
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
