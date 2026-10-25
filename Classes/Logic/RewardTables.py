"""What each Trophy Road tier and each Brawl Pass tier pays.

Ported from the BS-V29 LogicClaimSL and LogicClaimBP reward tables, which key
off the tier the client asks for. A tier the client asks for that is not in a
table is reported as None so the caller refuses it, rather than paying out
something the client did not ask for.

The boxes are the ones their LogicBoxDataCommand actually maps to: box 6 goes
out as 10, box 7 as 12, box 8 as 11, and LogicTropRoad uses box 100 for the
plain coin and power point payouts.
"""
from Classes.Logic.RewardDelivery import (
    BOX_MEGA,
    REWARD_BRAWLER,
    REWARD_BRAWLER_POINTS,
    REWARD_COINS,
    REWARD_GEMS,
    REWARD_SKIN,
)

BOX_PLAIN = 100

# The brawlers the Trophy Road hands out, keyed by tier.
TROPHY_ROAD_BRAWLERS = {
    2: 8, 6: 1, 10: 2, 15: 7, 25: 3, 35: 9, 45: 14, 55: 22, 65: 27, 75: 30,
}

# Coins, keyed by tier.
TROPHY_ROAD_COINS = {
    16: 50, 19: 50, 23: 50, 26: 50, 36: 50, 39: 50, 44: 50, 46: 50, 50: 50,
    54: 50, 71: 50, 74: 50,
    29: 100, 32: 100,
    41: 150, 63: 150, 81: 150, 83: 150,
    57: 200, 66: 200, 69: 200, 79: 200,
    48: 300,
    86: 500, 90: 500,
    94: 1000,
    # The two "tokens for level up" tiers are the plain coin payout too.
    7: 250, 51: 250,
    4: 500, 8: 500, 12: 500, 21: 500, 24: 500,
}

# Brawler power points, keyed by tier.
TROPHY_ROAD_POINTS = {
    9: 25, 13: 25, 17: 25, 22: 25, 43: 25, 47: 25, 53: 25, 59: 25, 61: 25,
    64: 25, 72: 25,
    30: 50, 34: 50, 82: 50,
    28: 75,
    38: 150, 56: 150, 68: 150, 77: 150,
    88: 200, 92: 200,
}

# Tiers that pay a box instead of a flat amount, as (box id the client asks
# for, box id that goes on the wire).
TROPHY_ROAD_BOXES = {
    1: (6, 10), 3: (6, 10), 4: (6, 10), 5: (6, 10),
    11: (6, 10), 14: (6, 10), 20: (6, 10), 27: (6, 10),
    37: (6, 10), 40: (6, 10), 42: (6, 10), 49: (6, 10),
    52: (6, 10), 62: (6, 10),

    18: (7, 12), 31: (7, 12), 33: (7, 12),
    58: (7, 12), 67: (7, 12), 73: (7, 12),
    76: (7, 12), 78: (7, 12), 84: (7, 12),

    60: (8, 11), 70: (8, 11), 80: (8, 11),
    85: (8, 11), 87: (8, 11), 89: (8, 11),
    91: (8, 11), 93: (8, 11),
}


def trophy_road_reward(tier, brawler=0):
    """The reward for a Trophy Road tier, or None when the tier pays a box."""
    tier = int(tier)
    if tier in TROPHY_ROAD_BOXES:
        return None
    if tier in TROPHY_ROAD_BRAWLERS:
        return [{"amount": 1, "reward_id": REWARD_BRAWLER,
                 "brawler": TROPHY_ROAD_BRAWLERS[tier]}]
    if tier in TROPHY_ROAD_COINS:
        return [{"amount": TROPHY_ROAD_COINS[tier], "reward_id": REWARD_COINS}]
    if tier in TROPHY_ROAD_POINTS:
        return [{"amount": TROPHY_ROAD_POINTS[tier],
                 "reward_id": REWARD_BRAWLER_POINTS,
                 "brawler": int(brawler or 0)}]
    if tier > 93:
        return None
    return None


def trophy_road_box(tier):
    """The box id a Trophy Road tier opens on the wire, or None.

    The first figure of the table entry is the box the client names, the
    second is the one that actually goes out, because their
    LogicBoxDataCommand remaps 6 to 10, 7 to 12 and 8 to 11.
    """
    entry = TROPHY_ROAD_BOXES.get(int(tier))
    if entry is None:
        return None
    return entry[1]


# The Brawl Pass free track, keyed by tier, from LogicClaimBP.encode.
BP_FREE = {
    0: (1, REWARD_COINS), 2: (1, REWARD_COINS), 4: (1, REWARD_COINS),
    6: (1, REWARD_COINS), 8: (1, REWARD_COINS), 12: (1, REWARD_COINS),
    14: (1, REWARD_COINS), 16: (1, REWARD_COINS), 18: (1, REWARD_COINS),
    21: (1, REWARD_COINS), 24: (1, REWARD_COINS), 26: (1, REWARD_COINS),
    29: (1, REWARD_COINS), 32: (1, REWARD_COINS), 34: (1, REWARD_COINS),
    37: (1, REWARD_COINS), 46: (1, REWARD_COINS), 49: (1, REWARD_COINS),
    52: (1, REWARD_COINS), 56: (1, REWARD_COINS), 58: (1, REWARD_COINS),
    42: (1, REWARD_COINS),
    3: (10, REWARD_GEMS), 15: (20, REWARD_GEMS), 23: (10, REWARD_GEMS),
    35: (10, REWARD_GEMS), 43: (10, REWARD_GEMS), 51: (20, REWARD_GEMS),
    7: (50, REWARD_COINS), 19: (50, REWARD_COINS),
    31: (100, REWARD_COINS), 47: (200, REWARD_COINS), 57: (500, REWARD_COINS),
    27: (50, REWARD_BRAWLER_POINTS),
}

# The premium track, keyed by tier, from LogicClaimBP.encode2.
BP_PREMIUM = {
    2: (100, REWARD_COINS), 4: (100, REWARD_COINS), 8: (100, REWARD_COINS),
    25: (100, REWARD_COINS),
    14: (200, REWARD_COINS), 21: (200, REWARD_COINS), 31: (500, REWARD_COINS),
    16: (20, REWARD_GEMS), 19: (20, REWARD_GEMS), 22: (20, REWARD_GEMS),
    24: (20, REWARD_GEMS), 26: (20, REWARD_GEMS), 28: (20, REWARD_GEMS),
    30: (20, REWARD_GEMS), 32: (20, REWARD_GEMS), 34: (20, REWARD_GEMS),
    36: (20, REWARD_GEMS), 38: (20, REWARD_GEMS), 40: (20, REWARD_GEMS),
    42: (20, REWARD_GEMS),
    1: (1, REWARD_BRAWLER), 3: (1, REWARD_BRAWLER), 7: (1, REWARD_BRAWLER),
    9: (1, REWARD_BRAWLER), 12: (1, REWARD_BRAWLER), 17: (1, REWARD_BRAWLER),
    20: (1, REWARD_BRAWLER), 27: (1, REWARD_BRAWLER), 35: (1, REWARD_BRAWLER),
    41: (1, REWARD_BRAWLER),
    0: (1, REWARD_COINS), 5: (1, REWARD_COINS), 10: (1, REWARD_COINS),
    23: (1, REWARD_COINS), 33: (1, REWARD_COINS), 37: (1, REWARD_COINS),
    43: (1, REWARD_SKIN),
    15: (1, REWARD_BRAWLER),
}

BP_PREMIUM_BRAWLERS = {15: 35, 43: 0}
BP_PREMIUM_SKINS = {43: 180}


def brawl_pass_reward(tier, premium, brawler=0):
    """The reward for a Brawl Pass tier on the named track, or None."""
    table = BP_PREMIUM if premium else BP_FREE
    entry = table.get(int(tier))
    if entry is None:
        return None
    amount, reward_id = entry

    reward = {"amount": amount, "reward_id": reward_id}
    if premium:
        if reward_id == REWARD_BRAWLER:
            reward["brawler"] = BP_PREMIUM_BRAWLERS.get(int(tier), brawler)
        elif reward_id == REWARD_SKIN:
            reward["skin"] = BP_PREMIUM_SKINS.get(int(tier), 0)
    elif reward_id in (REWARD_BRAWLER_POINTS, REWARD_BRAWLER):
        reward["brawler"] = int(brawler or 0)
    return [reward]