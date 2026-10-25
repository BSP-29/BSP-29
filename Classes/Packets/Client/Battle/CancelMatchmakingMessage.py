from Classes.Messaging import Messaging
from Classes.Packets.PiranhaMessage import PiranhaMessage
from Classes.TeamMatchmaking import cancel_matchmaking


class CancelMatchmakingMessage(PiranhaMessage):
    def __init__(self, messageData):
        super().__init__(messageData)
        self.messageVersion = 0

    def encode(self, fields):
        pass

    def decode(self):
        fields = {}
        super().decode(fields)
        return fields

    def execute(message, calling_instance, fields, cryptoInit):
        player = calling_instance.player
        team_id = getattr(player, "TeamID", [0, 0])
        room_id = int(team_id[1] or 0) if team_id and len(team_id) > 1 else 0
        if not cancel_matchmaking(room_id, reset_ready=True):
            Messaging.sendMessage(
                20406,
                {"Socket": calling_instance.client},
                cryptoInit,
                player,
            )

    def getMessageType(self):
        return 14106

    def getMessageVersion(self):
        return self.messageVersion
