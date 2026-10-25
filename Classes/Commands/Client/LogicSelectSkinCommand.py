from Classes.Commands.LogicCommand import LogicCommand
from Classes.Messaging import Messaging
from Classes.Files.Classes.Skins import Skins
from Classes.TeamManager import get_room, get_room_players


class LogicSelectSkinCommand(LogicCommand):
    def __init__(self, commandData):
        super().__init__(commandData)

    def encode(self, fields):
        LogicCommand.encode(self, fields)
        self.writeDataReference(0)
        return self.messagePayload

    def decode(self, calling_instance):
        fields = {}
        LogicCommand.decode(calling_instance, fields, False)
        fields["TargetSkin"] = calling_instance.readDataReference()
        LogicCommand.parseFields(fields)
        return fields

    def execute(self, calling_instance, fields, cryptoInit):
        player = calling_instance.player
        selected_brawler = Skins.getBrawlerBySkin(fields["TargetSkin"][1])
        player.SelectedSkins[selected_brawler] = fields["TargetSkin"][1]

        if hasattr(player, "TeamID") and player.TeamID and player.TeamID[1] != 0:
            room_low = int(player.TeamID[1] or 0)
            room = get_room(room_low)
            if room is None:
                print("[SELECT SKIN DEBUG] no room for TeamID", player.TeamID)
                return

            members = get_room_players(room_low)
            print("[SELECT SKIN DEBUG] broadcasting TeamMessage for room", room_low,
                  "members:", [getattr(member, "LowID", "?") for member in members])

            for member in members:
                session = getattr(member, "session", None)
                if session is None or not hasattr(session, "client") or not hasattr(session, "cryptoInit"):
                    print("[SELECT SKIN DEBUG] member", getattr(member, "LowID", "?"),
                          "has no session.client/cryptoInit, skipping")
                    continue

                Messaging.sendMessage(
                    24124,
                    {"Socket": session.client},
                    session.cryptoInit,
                    member
                )

    def getCommandType(self):
        return 506