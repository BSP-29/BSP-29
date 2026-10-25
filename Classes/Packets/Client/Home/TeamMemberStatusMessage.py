from Classes.Packets.PiranhaMessage import PiranhaMessage
from Classes.TeamManager import get_member_record, get_room


def _broadcast_team(room_id):
    """Route through the shared sender so members in a battle are skipped.

    The client sends 14361 again right after 20559 as it leaves the lobby.
    Answering it with 24124 would land a team lobby snapshot on top of the
    loading screen and pull the client back out of the match.
    """
    from Classes.TeamMatchmaking import broadcast_team
    broadcast_team(room_id)


class TeamMemberStatusMessage(PiranhaMessage):
    """v28 client packet that updates a member's STAT, pin, and mode."""

    def __init__(self, messageData):
        super().__init__(messageData)
        self.messageVersion = 0

    def encode(self, fields):
        pass

    def decode(self):
        fields = {}
        # v28 sends state, pin, and mode. Some v29 clients send only state.
        if self.offset < self.length:
            fields["state"] = self.readVInt()
        if self.offset < self.length:
            fields["pin"] = self.readVInt()
        if self.offset < self.length:
            fields["mode"] = self.readVInt()
        super().decode(fields)
        return fields

    def execute(message, calling_instance, fields, cryptoInit):
        player = calling_instance.player
        team_id = getattr(player, "TeamID", [0, 0])
        room_id = int(team_id[1] or 0) if team_id and len(team_id) > 1 else 0
        room = get_room(room_id)
        if room is None:
            return

        if "pin" in fields:
            player.pin = int(fields["pin"] or 0)
        if "mode" in fields:
            player.mode = int(fields["mode"] or 0)
        member_record = get_member_record(room_id, getattr(player, "LowID", 0))
        if member_record is None:
            return

        if "state" in fields:
            member_record["STAT"] = int(fields["state"] or 0)
        _broadcast_team(room_id)

    def getMessageType(self):
        return 14361

    def getMessageVersion(self):
        return self.messageVersion
