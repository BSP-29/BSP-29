import json
import os
import random

_BOX_CONFIG_PATH = os.path.join(
    os.path.dirname(__file__), "..", "Logic", "reward_tables.json"
)

_BOX_CONFIG_MTIME = 0
_BOX_CONFIG_CACHE = {}


def _load_box_config():
    """Hot-reload box_config from reward_tables.json."""
    global _BOX_CONFIG_MTIME, _BOX_CONFIG_CACHE
    try:
        mtime = os.path.getmtime(_BOX_CONFIG_PATH)
    except OSError:
        return _BOX_CONFIG_CACHE
    if mtime != _BOX_CONFIG_MTIME:
        try:
            with open(_BOX_CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            _BOX_CONFIG_CACHE = data.get("box_config", {})
            _BOX_CONFIG_MTIME = mtime
        except Exception:
            pass
    return _BOX_CONFIG_CACHE


def generate_box_rewards(box_id):
    """Generate reward list based on box_config probabilities.

    For box_id 100: returns None (caller uses JSON amount/item_id).
    For 10/11/12: generates 2-8 rewards with coin/gem ranges.
    """
    config = _load_box_config()
    cfg = config.get(str(box_id))
    if not cfg:
        return None

    # Box 100: use JSON values, single reward
    if box_id == 100 and cfg.get("use_json_amount"):
        return None

    # Determine number of rewards
    rc = cfg.get("rewards_count", {"1": 1.0})
    r = random.random()
    cumulative = 0.0
    num_rewards = 2  # default
    for key, prob in rc.items():
        cumulative += prob
        if r <= cumulative:
            # key can be "2", "2-4", "5-6", "7-8"
            if "-" in key:
                lo, hi = key.split("-")
                num_rewards = random.randint(int(lo), int(hi))
            else:
                num_rewards = int(key)
            break

    coin_range = cfg.get("coin_range", [10, 100])
    gem_range = cfg.get("gem_range", [1, 3])
    coin_chance = cfg.get("coin_chance", 0.99)
    gem_chance = cfg.get("gem_chance", 0.01)

    rewards = []
    for _ in range(num_rewards):
        if random.random() < coin_chance:
            amt = random.randint(coin_range[0], coin_range[1])
            rewards.append({"amount": amt, "reward_id": 7})  # coins
        else:
            amt = random.randint(gem_range[0], gem_range[1])
            rewards.append({"amount": amt, "reward_id": 8})  # gems

    return rewards if rewards else [{"amount": 1, "reward_id": 7}]