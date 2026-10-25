from Classes.Packets.PiranhaMessage import PiranhaMessage
from Classes.TeamManager import get_room_players, remove_player_from_room, get_room
from Classes.Messaging import Messaging
from Classes.TeamMatchmaking import cancel_matchmaking


def handle_leave_team(calling_instance, cryptoInit):
    player = calling_instance.player

    if not player.TeamID or player.TeamID[1] == 0:
        return

    room_id = int(player.TeamID[1] or 0)
    if get_room(room_id) is None:
        return

    room = get_room(room_id)
    if room is not None and room.get("matchmakingStarted"):
        # Leaving the room cancels its shared search before membership changes.
        cancel_matchmaking(room_id, reset_ready=True)

    room_after = remove_player_from_room(room_id, player)

    # remove_player_from_room returns None once the last member is gone. The
    # chat stream was never released here, so its per-room entry list grew for
    # the whole process lifetime.
    if room_after is None:
        from Classes.Packets.Server.Home.TeamStream2 import TeamStream2
        TeamStream2.delete_room(room_id)

    if room_after is not None:
        for member in get_room_players(room_id):
            session = getattr(member, "session", None)
            if not session or not hasattr(session, "client") or not hasattr(session, "cryptoInit"):
                continue

            Messaging.sendMessage(
                24124,
                {"Socket": session.client},
                session.cryptoInit,
                member
            )

    if hasattr(player, "session") and player.session is not None:
        session = player.session
        if hasattr(session, "client") and hasattr(session, "cryptoInit"):
            Messaging.sendMessage(
                24125,
                {"Socket": session.client},
                session.cryptoInit,
                player
            )


class TeamLeftMessage(PiranhaMessage):
    def __init__(self, messageData):
        super().__init__(messageData)
        self.messageVersion = 0

    def encode(self, fields, player):
        self.writeInt(0)

    def decode(self):
        return {}

    def execute(message, calling_instance, fields):
        pass

    def getMessageType(self):
        return 24125

    def getMessageVersion(self):
        return self.messageVersion
