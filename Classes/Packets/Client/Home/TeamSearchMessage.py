from Classes.ClientsManager import ClientsManager
from Classes.Messaging import Messaging
from Classes.Packets.PiranhaMessage import PiranhaMessage
from Classes.TeamManager import Teams, add_player_to_room, get_room, get_room_players


def _has_online_member(room_id):
    online = ClientsManager.GetAll()
    for member in get_room_players(room_id):
        player_id = int(getattr(member, "LowID", 0) or 0)
        client_data = online.get(player_id)
        session = getattr(member, "session", None)
        if client_data and session is not None and client_data.get("Session") is session:
            return True
    return False


def _broadcast_team(room_id, calling_instance, crypto_init):
    from Classes.TeamMatchmaking import member_is_in_battle

    for member in get_room_players(room_id):
        # A member that is already in a battle must not be pulled back to the
        # lobby by a snapshot sent for a different room's search.
        if member_is_in_battle(member):
            continue
        session = getattr(member, "session", None)
        if session is not None and hasattr(session, "client") and hasattr(session, "cryptoInit"):
            Messaging.sendMessage(
                24124,
                {"Socket": session.client},
                session.cryptoInit,
                member,
            )
        elif member is calling_instance.player:
            Messaging.sendMessage(
                24124,
                {"Socket": calling_instance.client},
                crypto_init,
                member,
            )


class TeamSearchMessage(PiranhaMessage):
    """Finds the first active v28-style open team with a free player slot."""

    def __init__(self, messageData):
        super().__init__(messageData)
        self.messageVersion = 0

    def encode(self, fields):
        pass

    def decode(self):
        fields = {}
        # The v28 request contains one VInt; the reference handler doesn't use it.
        if self.offset < self.length:
            fields["request"] = self.readVInt()
        super().decode(fields)
        return fields

    def execute(message, calling_instance, fields, cryptoInit):
        player = calling_instance.player
        current_team_id = getattr(player, "TeamID", [0, 0])
        current_room_id = (
            int(current_team_id[1] or 0)
            if isinstance(current_team_id, (list, tuple)) and len(current_team_id) > 1
            else 0
        )

        for room in list(Teams):
            room_id = int(room.get("id", 0) or 0)
            members = room.get("players", [])
            if room_id == current_room_id or not room_id:
                continue
            if len(members) >= 3 or not _has_online_member(room_id):
                continue

            joined_room = add_player_to_room(room_id, player)
            if joined_room is None:
                continue

            # Moving between teams changes the old room too; refresh its
            # remaining members after the join succeeded.
            if current_room_id:
                old_room = get_room(current_room_id)
                if old_room is not None:
                    _broadcast_team(current_room_id, calling_instance, cryptoInit)
            _broadcast_team(room_id, calling_instance, cryptoInit)
            return

    def getMessageType(self):
        return 14199

    def getMessageVersion(self):
        return self.messageVersion
