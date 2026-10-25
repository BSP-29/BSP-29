from Classes.Commands.LogicCommand import LogicCommand
from Classes.Logic.BrawlerLoadout import resolve_power_level
from Classes.Messaging import Messaging
from Classes.TeamManager import get_room, get_room_players


class LogicSelectCharacterCommand(LogicCommand):
    def __init__(self, commandData):
        super().__init__(commandData)

    def encode(self, fields):
        LogicCommand.encode(self, fields)
        self.writeDataReference(0)
        return self.messagePayload

    def decode(self, calling_instance):
        fields = {}
        LogicCommand.decode(calling_instance, fields, False)
        fields["TargetCharacter"] = calling_instance.readDataReference()
        LogicCommand.parseFields(fields)
        return fields

    def execute(self, calling_instance, fields, cryptoInit):
        player = calling_instance.player
        target_brawler_id = fields["TargetCharacter"][1]

        player.SelectedBrawler = int(target_brawler_id)
        if hasattr(player, "_db_dyn") and player._db_dyn is not None:
            player._db_dyn.set_selected_brawler(target_brawler_id)

        # The old guard was "elif BrawlerLevel < 1", which is inverted: it only
        # fired when the level was already invalid and never clamped a valid
        # one. Brawlers at id 100 or more are held at 9, everything else at 10.
        player.BrawlerLevel = resolve_power_level(player, player.SelectedBrawler)

        if hasattr(player, "TeamID") and player.TeamID and player.TeamID[1] != 0:
            room_low = int(player.TeamID[1] or 0)
            room = get_room(room_low)
            if room is None:
                print("[SELECT CHAR DEBUG] no room for TeamID", player.TeamID)
                return

            members = get_room_players(room_low)
            print("[SELECT CHAR DEBUG] broadcasting TeamMessage for room", room_low,
                  "members:", [getattr(member, "LowID", "?") for member in members])

            for member in members:
                session = getattr(member, "session", None)
                if session is None or not hasattr(session, "client") or not hasattr(session, "cryptoInit"):
                    print("[SELECT CHAR DEBUG] member", getattr(member, "LowID", "?"),
                          "has no session.client/cryptoInit, skipping")
                    continue

                Messaging.sendMessage(
                    24124,
                    {"Socket": session.client},
                    session.cryptoInit,
                    member
                )

    def getCommandType(self):
        return 525