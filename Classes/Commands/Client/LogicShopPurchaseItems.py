"""24111 / 519, shop purchase.

Ported from the BS-V29 LogicPurchaseOfferCommand. The original read the
command id from the client, which is not how this server works, so it is
registered as command 519 and decodes the offer index itself.

The client sends the offer index and the server deducts the cost and grants
whatever the offer carries: a box, gems, gold, a brawler, a skin or a star
power. Each grant goes out through LogicGiveDeliveryItems so the client plays
the same animation it plays for any other reward.
"""
from Classes.Commands.LogicCommand import LogicCommand
from Classes.Logic.RewardDelivery import (
    BOX_MEGA,
    REWARD_BRAWLER,
    REWARD_BRAWLER_POINTS,
    REWARD_COINS,
    REWARD_GEMS,
    REWARD_SKIN,
    send_delivery,
)


class LogicShopPurchaseItems(LogicCommand):
    """Handles a shop purchase for a single offer."""

    def __init__(self, commandData):
        super().__init__(commandData)

    def encode(self, fields):
        LogicCommand.encode(self, fields)
        return self.messagePayload

    def decode(self, calling_instance):
        fields = {}
        LogicCommand.decode(calling_instance, fields, False)
        # The offer index is the last VInt the client sends.
        fields["OfferIndex"] = calling_instance.readVInt()
        LogicCommand.parseFields(fields)
        return fields

    def execute(self, calling_instance, fields, cryptoInit):
        player = calling_instance.player
        # The command header carries ExecutorAccountID which the client sends
        # as -1, -1. Use the player's own LowID from the DB instead.
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
        # High ID is always 0 for this server.
        player.HighID = 0
        player.ID = [0, int(getattr(player, "LowID", 0) or 0)]
        offer_index = int(fields.get("OfferIndex", 0) or 0)

        # The offer shapes this server supports. Each one deducts its own
        # currency and grants its own reward through 24111.
        offers = {
            # offer_index: (currency, cost, reward)
            # Offer 0 costs 0 gems (free) — the executor id comes from player.LowID
            0: ("gems", 0, [{"amount": 1, "reward_id": 6, "box_id": BOX_MEGA}]),
            1: ("gems", 30, [{"amount": 1, "reward_id": 6, "box_id": BOX_MEGA}]),
            2: ("gold", 100, [{"amount": 1, "reward_id": 7, "amount": 100}]),
            3: ("gems", 5, [{"amount": 5, "reward_id": REWARD_GEMS}]),
            4: ("gems", 10, [{"amount": 10, "reward_id": REWARD_GEMS}]),
        }

        offer = offers.get(offer_index)
        if offer is None:
            print(f"[Shop] unknown offer {offer_index}, ignored")
            return

        currency, cost, rewards = offer
        database = getattr(player, "_db_dyn", None)

        if currency == "gems":
            if int(getattr(player, "Gems", 0) or 0) < cost:
                print(f"[Shop] offer {offer_index}: not enough gems")
                return
            if database is not None:
                database.set_gems(int(player.Gems) - cost)
            player.Gems = int(player.Gems) - cost
        elif currency == "gold":
            if int(getattr(player, "Coins", 0) or 0) < cost:
                print(f"[Shop] offer {offer_index}: not enough gold")
                return
            if database is not None:
                database.set_coins(int(player.Coins) - cost)
            player.Coins = int(player.Coins) - cost

        session = getattr(calling_instance, "session", None) or player.session
        crypto = getattr(session, "cryptoInit", None)

        for reward in rewards:
            box_id = reward.pop("box_id", None)
            send_delivery(
                session, crypto, player,
                [reward],
                box_id=box_id if box_id else BOX_MEGA,
                track_type=1,
                reward_rank=0,
            )

        print(f"[Shop] offer {offer_index} purchased for {cost} {currency}")

    def getCommandType(self):
        return 519