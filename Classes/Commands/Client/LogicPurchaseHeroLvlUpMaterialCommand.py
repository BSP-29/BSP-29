"""521, LogicPurchaseHeroLvlUpMaterial.

Ported from BS-V29 LogicPurchaseHeroLvlUpMaterialCommand.
The client sends 4 header VInts (consumed by LogicCommand.decode) plus a
gold amount VInt. The server grants 1007 gold and deducts 10 gems.
"""
from Classes.Commands.LogicCommand import LogicCommand
from Classes.Logic.RewardDelivery import (
    REWARD_COINS,
    send_delivery,
)


class LogicPurchaseHeroLvlUpMaterialCommand(LogicCommand):

    def __init__(self, commandData):
        super().__init__(commandData)

    def encode(self, fields):
        LogicCommand.encode(self, fields)
        return self.messagePayload

    def decode(self, calling_instance):
        fields = {}
        LogicCommand.decode(calling_instance, fields, False)
        fields["Gold"] = calling_instance.readVInt()
        LogicCommand.parseFields(fields)
        return fields

    def execute(self, calling_instance, fields, cryptoInit):
        player = calling_instance.player
        if int(getattr(player, "LowID", 0) or 0) <= 0:
            try:
                token = getattr(player, "Token", "")
                if token:
                    from Classes.DB.DynamicDB import DynamicDB
                    low = DynamicDB.find_lowid_by_token(token)
                    if low is not None:
                        player.LowID = int(low)
            except Exception:
                pass
        player.HighID = 0
        player.ID = [0, int(getattr(player, "LowID", 0) or 0)]

        database = getattr(player, "_db_dyn", None)
        cost = 10
        value = 1007

        if int(getattr(player, "Gems", 0) or 0) < cost:
            print(f"[PurchaseHeroLvlUpMaterial] not enough gems")
            return

        new_gold = int(getattr(player, "Coins", 0) or 0) + value
        new_gems = int(getattr(player, "Gems", 0) or 0) - cost

        if database is not None:
            if hasattr(database, "set_coins"):
                database.set_coins(new_gold)
            if hasattr(database, "set_gems"):
                database.set_gems(new_gems)
        player.Coins = new_gold
        player.Gems = new_gems

        session = getattr(calling_instance, "session", None) or getattr(player, "session", None)
        crypto = getattr(session, "cryptoInit", None) if session else None
        if session is not None and getattr(session, "client", None) is not None:
            send_delivery(
                session, crypto, player,
                [{"amount": value, "reward_id": REWARD_COINS}],
                box_id=100,
                track_type=1,
                reward_rank=0,
            )

        print(f"[PurchaseHeroLvlUpMaterial] granted {value} gold for {cost} gems")

    def getCommandType(self):
        return 521
