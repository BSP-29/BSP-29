from Classes.Packets.PiranhaMessage import PiranhaMessage
from Classes.TeamManager import get_member_record, get_room
from Classes.TeamMatchmaking import (
    all_members_ready,
    broadcast_team,
    cancel_matchmaking,
    start_matchmaking,
)


class TeamSetMemberReadyMessage(PiranhaMessage):
    """Toggle the sender's ready flag and refresh the room for every member."""

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
        if get_room(room_id) is None:
            return

        member_record = get_member_record(room_id, getattr(player, "LowID", 0))
        if member_record is None:
            return

        player.isReady = not bool(getattr(player, "isReady", False))
        member_record["READY"] = player.isReady

        room = get_room(room_id)
        if room is not None and room.get("matchmakingStarted") and not player.isReady:
            # Any member becoming unready cancels the shared search.
            cancel_matchmaking(room_id, reset_ready=False)

        should_start_matchmaking = all_members_ready(room_id)

        # Route through the shared sender. This used to have its own inline
        # loop, which sent the snapshot with no battle guard and produced a
        # second copy immediately after the one start_matchmaking sends.
        broadcast_team(room_id)

        # Send the queue transition after the room snapshot so the final packet
        # tells each client to leave the lobby and show matchmaking.
        if should_start_matchmaking:
            start_matchmaking(room_id)

    def getMessageType(self):
        return 14355

    def getMessageVersion(self):
        return self.messageVersion
