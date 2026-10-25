from Classes.Packets.PiranhaMessage import PiranhaMessage
from Classes.Messaging import Messaging
from Classes.TeamManager import add_player_to_room, get_room_players


class TeamSpectateMessage(PiranhaMessage):
    def __init__(self, messageData):
        super().__init__(messageData)
        self.messageVersion = 0

    def encode(self, fields):
        pass

    def decode(self):
        fields = {}
        fields["roomHigh"] = self.readVInt()
        fields["room_id"] = self.readVInt()
        fields["roomType"] = self.readVInt()
        super().decode(fields)
        return fields

    def execute(message, calling_instance, fields, cryptoInit):
        player = calling_instance.player
        room_id = int(fields.get("room_id", 0) or 0)
        room_type = int(fields.get("roomType", 0) or 0)

        print("[TeamSpectate] execute for player",
              getattr(player, "LowID", 0),
              "client room_id:", room_id,
              "client roomType:", room_type,
              "current TeamID:", getattr(player, "TeamID", None))

        if room_id == 0:
            print("[TeamSpectate] invalid room_id 0 from client, abort")
            return

        try:
            room = add_player_to_room(room_id, player)
            if room is None:
                print("[TeamSpectate] add_player_to_room failed for room_id", room_id)
                return

            # The room type belongs to its owner and is immutable for joiners.
            members = get_room_players(room_id)

            print("[TeamSpectate] room", room_id,
                  "roomType:", room_type,
                  "players:", [getattr(member, "LowID", 0) for member in members])

            for member in members:
                session = getattr(member, "session", None)
                if not session or not hasattr(session, "client") or not hasattr(session, "cryptoInit"):
                    print("[TeamSpectate] member", getattr(member, "LowID", 0),
                          "missing session/crypto, skip")
                    continue

                Messaging.sendMessage(
                    24124,
                    {"Socket": session.client},
                    session.cryptoInit,
                    member
                )

        except Exception as e:
            import traceback
            print("[TeamSpectate] error:", e)
            traceback.print_exc()

    def getMessageType(self):
        return 14358

    def getMessageVersion(self):
        return self.messageVersion