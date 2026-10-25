"""The Brawl Pass Pro token ladder, and what a tier pays.

The BS-V29 version walks the ladder with an if/elif chain:

    if   0 <= t <= 75:  t += 75
    elif 75 < t <= 150: t += 100
    ...
    elif 250 < t <= 600: t += 300     # unreachable, 250 < t <= 400 already ran
    elif 250 < t >= 900: t += 400     # unreachable, and a >= against <
    elif t >= 6500: t += 500          # unreachable

Every arm after the sixth is dead, so a player past 900 tokens gains nothing.
The ladder is rebuilt here as one monotonic table instead. The six live arms
are kept exactly as they were, because those are the ones that actually ran
and therefore the ones the client has seen.

The cost of a tier is the distance between two thresholds, so "which tier can
this player afford" and "what does tier n cost" cannot disagree.
"""

# The six costs the original if/elif chain really applied, in order.
_LIVE_COSTS = (75, 100, 150, 200, 300, 300)

# Past the part that ever ran, the chain's unreachable arms name the next
# figures: 400, then 500, 550, 600 and 650. Kept here so the ladder continues
# instead of stalling at 900.
_EXTENDED_COSTS = (400, 450, 500, 550, 600, 650)

COSTS = _LIVE_COSTS + _EXTENDED_COSTS

# THRESHOLD[i] is the smallest token count that unlocks tier i, so it is the
# running sum of the costs before it. Tier 0 is free.
THRESHOLDS = [0]
for _cost in COSTS:
    THRESHOLDS.append(THRESHOLDS[-1] + _cost)


def tokens_needed_for_tier(tier: int) -> int:
    """How many Pro tokens tier n costs, counted from zero."""
    tier = max(0, int(tier))
    if tier >= len(THRESHOLDS):
        return THRESHOLDS[-1]
    return THRESHOLDS[tier]


def cost_of_tier(tier: int) -> int:
    """What one tier of Pro tokens costs."""
    tier = max(0, int(tier))
    if tier == 0:
        return 0
    return tokens_needed_for_tier(tier) - tokens_needed_for_tier(tier - 1)


def tokens_for_tier_after(tokens: int, cost: int = 0) -> int:
    """Add one tier's worth of tokens to a total.

    The original walked bands whose boundaries do not line up with the running
    sum: it charged 150 up to a boundary of 250 while the sum put the tier 3
    threshold at 325, so its band costs and its thresholds disagreed and a
    player at 300 tokens was credited 200 when the tier had cost 150. Here a
    total earns the cost of the next tier the player has not reached, which is
    what the first two arms of the original did and what keeps agreeing with
    it wherever the original was self consistent.
    """
    tokens = max(0, int(tokens))
    return tokens + cost_of_tier(tier_for_tokens(tokens) + 1)


def tier_for_tokens(tokens: int) -> int:
    """The highest tier this many tokens unlocks."""
    tokens = max(0, int(tokens))
    tier = 0
    while (tier + 1 < len(THRESHOLDS)
           and tokens >= THRESHOLDS[tier + 1]):
        tier += 1
    return tier


def can_afford(tokens: int, tier: int) -> bool:
    return max(0, int(tokens)) >= tokens_needed_for_tier(tier)