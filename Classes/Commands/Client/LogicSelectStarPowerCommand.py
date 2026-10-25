from Classes.Commands.LogicCommand import LogicCommand
from Classes.Messaging import Messaging
from Classes.Files.Classes.Cards import Cards
from Classes.TeamManager import get_room, get_room_players


class LogicSelectStarPowerCommand(LogicCommand):
    def __init__(self, commandData):
        super().__init__(commandData)

    def encode(self, fields):
        LogicCommand.encode(self, fields)
        self.writeDataReference(0)
        return self.messagePayload

    def decode(self, calling_instance):
        fields = {}
        LogicCommand.decode(calling_instance, fields, False)
        fields["TargetCard"] = calling_instance.readDataReference()
        LogicCommand.parseFields(fields)
        return fields

    def execute(self, calling_instance, fields, cryptoInit):
        player = calling_instance.player
        card_type, card_id = fields["TargetCard"]

        owner_brawler = Cards.getOwner(card_id)
        brawler_id = int(owner_brawler)

        print("[SELECT DEBUG]",
              "card_type:", card_type,
              "card_id:", card_id,
              "owner_brawler:", owner_brawler,
              "brawler_id:", brawler_id,
              "SelectedBrawler:", player.SelectedBrawler)

        player.EquippedCards[brawler_id] = card_id
        if hasattr(player, "_db_dyn") and player._db_dyn is not None:
            player._db_dyn.set_brawler_equipped_card(brawler_id, card_id)

        if hasattr(player, "TeamID") and player.TeamID and player.TeamID[1] != 0:
            room_low = int(player.TeamID[1] or 0)
            room = get_room(room_low)
            if room is None:
                print("[SELECT DEBUG] no room for TeamID", player.TeamID)
                return

            members = get_room_players(room_low)
            print("[SELECT DEBUG] broadcasting TeamMessage for room", room_low,
                  "members:", [getattr(member, "LowID", "?") for member in members])

            for member in members:
                session = getattr(member, "session", None)
                if session is None or not hasattr(session, "client") or not hasattr(session, "cryptoInit"):
                    print("[SELECT DEBUG] member", getattr(member, "LowID", "?"),
                          "has no session.client/cryptoInit, skipping")
                    continue

                Messaging.sendMessage(
                    24124,
                    {"Socket": session.client},
                    session.cryptoInit,
                    member
                )

    def getCommandType(self):
        return 529