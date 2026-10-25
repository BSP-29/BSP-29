from Classes.Messaging import Messaging
from Classes.Packets.PiranhaMessage import PiranhaMessage
from Classes.TeamManager import get_room, set_room_map


class TeamSetLocationMessage(PiranhaMessage):
    def __init__(self, messageData):
        super().__init__(messageData)
        self.messageVersion = 0

    def encode(self, fields):
        pass

    def decode(self):
        fields = {}
        fields["location"] = self.readDataReference()
        super().decode(fields)
        return fields

    def execute(message, calling_instance, fields, cryptoInit):
        player = calling_instance.player
        map_id = int(fields["location"][1])
        player.SelectedMap = map_id

        team_id = getattr(player, "TeamID", [0, 0])
        room_id = int(team_id[1] or 0) if team_id and len(team_id) > 1 else 0
        room = get_room(room_id)
        if room is not None:
            owner = next(
                (entry for entry in room.get("players", []) if entry.get("OWNER")),
                None,
            )
            if owner and int(owner.get("plrID", 0) or 0) == int(player.LowID):
                set_room_map(room_id, map_id)

        from Classes.TeamMatchmaking import member_is_in_battle
        if member_is_in_battle(player):
            # Already loading a battle. A lobby snapshot here would undo 20559.
            return

        fields["Socket"] = calling_instance.client
        Messaging.sendMessage(24124, fields, cryptoInit, player)

    def getMessageType(self):
        return 14363

    def getMessageVersion(self):
        return self.messageVersion