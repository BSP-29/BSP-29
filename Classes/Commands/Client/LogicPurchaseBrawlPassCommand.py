"""534, buying the Brawl Pass.

Only the purchase itself lives here. The premium track tier is advanced by
536, the same place the free track is, so buying does not silently hand out a
tier the client has not asked for yet.
"""
from Classes.Commands.LogicCommand import LogicCommand

BRAWL_PASS_PRICE = 169


class LogicPurchaseBrawlPassCommand(LogicCommand):
    def __init__(self, commandData):
        super().__init__(commandData)

    def encode(self, fields):
        LogicCommand.encode(self, fields)
        return self.messagePayload

    def decode(self, calling_instance):
        fields = {}
        LogicCommand.decode(calling_instance, fields, False)
        LogicCommand.parseFields(fields)
        return fields

    def execute(self, calling_instance, fields, cryptoInit):
        player = calling_instance.player
        database = getattr(player, "_db_dyn", None)
        if database is None:
            return

        if database.get_brawl_pass_bought():
            print("[Pass] brawl pass already bought, ignoring a second purchase")
            return

        gems = int(getattr(player, "Gems", 0) or 0)
        if gems < BRAWL_PASS_PRICE:
            print(f"[Pass] not enough gems for the brawl pass: {gems} < "
                  f"{BRAWL_PASS_PRICE}")
            return

        database.set_gems(gems - BRAWL_PASS_PRICE)
        player.Gems = gems - BRAWL_PASS_PRICE
        database.set_brawl_pass_bought(True)
        print(f"[Pass] brawl pass bought for {BRAWL_PASS_PRICE} gems, "
              f"{player.Gems} left")

    def getCommandType(self):
        return 534