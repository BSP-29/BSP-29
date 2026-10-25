"""24111 reward delivery, Royale v29 layout. Dynamic amount/type via rewards list."""
import random

from Classes.Commands.LogicCommand import LogicCommand
from Classes.Messaging import Messaging

GIVE_DELIVERY_ITEMS = 203

REWARD_COINS = 7
REWARD_GEMS = 8
REWARD_BRAWLER = 1
REWARD_BRAWLER_POINTS = 6
REWARD_SKIN = 9
REWARD_TOKEN_DOUBLER = 2
REWARD_STARP_POWER = 4
REWARD_POWER_POINTS = 6
REWARD_UNLOCK_HERO = 1
REWARD_EMOTE = 10

TRACK_TROPHY_ROAD = 6
TRACK_BRAWL_PASS = 10 # 9 for Premium

BOX_MEGA = 100
BOX_GENERIC = 100

PREMIUM_AMOUNTS = {
    0: 10, 2: 100, 4: 100, 8: 100, 10: 100, 14: 200, 15: 10,
    16: 10, 18: 10, 21: 10, 23: 200, 25: 200, 26: 10, 29: 10,
    32: 10, 35: 10, 36: 200, 38: 10, 40: 10, 42: 10, 44: 10,
    46: 10, 48: 10, 50: 10, 51: 10,
}


def _vint(value):
    if value < 0:
        return bytes([(value & 0x3F) | 0x40])
    if value < 0x40:
        return bytes([value & 0x3F])
    if value < 0x2000:
        return bytes([(value & 0x3F) | 0x80, (value >> 6) & 0x7F])
    if value < 0x100000:
        return bytes([(value & 0x3F) | 0x80,
                      ((value >> 6) & 0x7F) | 0x80, (value >> 13) & 0x7F])
    if value < 0x8000000:
        return bytes([(value & 0x3F) | 0x80,
                      ((value >> 6) & 0x7F) | 0x80,
                      ((value >> 13) & 0x7F) | 0x80, (value >> 20) & 0x7F])
    return bytes([(value & 0x3F) | 0x80, ((value >> 6) & 0x7F) | 0x80,
                  ((value >> 13) & 0x7F) | 0x80, ((value >> 20) & 0x7F) | 0x80,
                  (value >> 27) & 0xF])


def _dataref(global_id):
    gid = int(global_id or 0)
    if gid <= 0:
        return _vint(0)
    cls = gid // 1000000
    inst = gid % 1000000
    return _vint(cls) + _vint(inst)


def _reward_class(reward):
    rid = int(reward.get("reward_id", REWARD_COINS) or 0)
    if rid in (REWARD_BRAWLER, REWARD_BRAWLER_POINTS, REWARD_POWER_POINTS,
               REWARD_UNLOCK_HERO):
        return 16
    if rid == REWARD_SKIN or rid == REWARD_STARP_POWER:
        return 20
    return 0


def pass_reward_amount(tier, premium):
    """Helper: returns coin amount for a pass tier."""
    if premium:
        return PREMIUM_AMOUNTS.get(int(tier), 1)
    return 1


def build_delivery(rewards, box_id=BOX_GENERIC, track_type=TRACK_BRAWL_PASS,
                   reward_rank=0, brawl_pass_season=0):
    rewards = list(rewards or [])
    if not rewards:
        rewards = [{"amount": 1, "reward_id": REWARD_COINS}]

    out = bytearray()
    out += _vint(203)
    out += _vint(0)
    out += _vint(1)                # DeliveryUnits.Count
    out += _vint(box_id)              # DeliveryUnit.Type
    out += _vint(len(rewards))     # Drops.Count
    for r in rewards:
        rid = int(r.get("reward_id", REWARD_COINS) or 0)
        amt = int(r.get("amount", 0))
        cls = _reward_class(r)
        if "cls" in r:
            cls = int(r.get("cls") or cls)
        out += _vint(amt)          # Count
        out += _dataref(int(r.get("data_global_id", 0) or 0))  # DataGlobalId
        out += _vint(rid)          # Type
        out += _dataref(int(r.get("skin_global_id", 0) or 0))  # SkinGlobalId
        out += _dataref(int(r.get("pin_global_id", 0) or 0))    # PinGlobalId
        out += _dataref(int(r.get("card_global_id", 0) or 0))  # CardGlobalId
        out += _vint(0)            # trailing 0
    out += _vint(0)                # forced drops
    out += _vint(0)                # RewardTrackType
    out += _vint(0)                # RewardForRank
    out += _vint(0)                # BrawlPassSeason
    out += _vint(1)                # unknown unused
    # base.Encode
    out += _vint(1)
    out += _vint(1)
    out += _vint(0)
    out += _vint(0)
    return bytes(out)


def grant(player, rewards):
    if player is None:
        return
    database = getattr(player, "_db_dyn", None)

    for reward in rewards or []:
        amount = int(reward.get("amount", 0) or 0)
        reward_id = int(reward.get("reward_id", 0) or 0)

        if reward_id == REWARD_COINS:
            if database is not None and hasattr(database, "add_coins"):
                database.add_coins(amount)
            player.Coins = int(getattr(player, "Coins", 0) or 0) + amount
        elif reward_id == REWARD_GEMS:
            if database is not None and hasattr(database, "add_gems"):
                database.add_gems(amount)
            player.Gems = int(getattr(player, "Gems", 0) or 0) + amount


def random_resource_rewards(count=None):
    return [{"amount": 100, "reward_id": REWARD_COINS}]


def send_delivery(session, crypto_init, player, rewards, box_id=BOX_GENERIC,
                  track_type=TRACK_BRAWL_PASS, reward_rank=0,
                  brawl_pass_season=0):
    rewards = list(rewards or [])
    if not rewards:
        return False
    if session is None or getattr(session, "client", None) is None:
        return False

    payload = build_delivery(rewards, box_id, track_type, reward_rank,
                             brawl_pass_season)
    print(f"[24111] delivering reward to account {getattr(player, 'LowID', '?')}")
    Messaging.sendMessage(
        24111,
        {
            "Socket": session.client,
            "Payload": payload,
            "Command": {"ID": GIVE_DELIVERY_ITEMS},
        },
        crypto_init,
        player,
    )
    return True
