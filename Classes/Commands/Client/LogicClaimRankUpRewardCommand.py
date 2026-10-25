"""517, LogicClaimRankUpReward.

bp field "a": 6=trophy road, 9=premium, 10=free.
season field "g": season index (e.g. 2 = season 3).
tier field "j": tier (0-based).
Rewards loaded from Classes/Logic/PassRewards.json.

Every claim is recorded on the caller's own database. A replayed claim for an
already-taken threshold:
- If account has CanMultiTier=true -> grant reward anyway (admin override)
- Otherwise -> send OutOfSyncMessage (24104) and reject
"""
import json
import os

from Classes.Commands.LogicCommand import LogicCommand
from Classes.Logic.BoxConfig import generate_box_rewards
from Classes.Logic.RewardDelivery import (
    REWARD_COINS,
    REWARD_GEMS,
    BOX_MEGA,
    send_delivery,
)
from Classes.Messaging import Messaging
from Classes.Packets.Server.Authentification.OutOfSyncMessage import OutOfSyncMessage

_PASS_REWARDS_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "Logic", "PassRewards.json"
)

_PASS_REWARDS_MTIME = 0
_PASS_REWARDS_CACHE = {"seasons": {}}


def _load_pass_rewards():
    """Hot-reload PassRewards.json when the file changes on disk."""
    global _PASS_REWARDS_MTIME, _PASS_REWARDS_CACHE
    try:
        mtime = os.path.getmtime(_PASS_REWARDS_PATH)
    except OSError:
        return _PASS_REWARDS_CACHE
    if mtime != _PASS_REWARDS_MTIME:
        try:
            with open(_PASS_REWARDS_PATH, "r", encoding="utf-8") as _f:
                _PASS_REWARDS_CACHE = json.load(_f)
            _PASS_REWARDS_MTIME = mtime
            print(f"[517] PassRewards.json reloaded (mtime={mtime})")
        except Exception as _e:
            print(f"[517] failed to load PassRewards.json: {_e}")
    return _PASS_REWARDS_CACHE


# Initial load
PASS_REWARDS = _load_pass_rewards()

TRACK_TROPHY_ROAD_ID = 6
TRACK_BRAWL_PASS_PREMIUM = 9
TRACK_BRAWL_PASS_FREE = 10
TRACK_BRAWL_PASS = 1
TRACK_TROPHY_ROAD = 6

VALID_BOX_IDS = {100, 10, 11, 12}


def _pass_reward(season, track, tier):
    """Return (amount, item_id, box_id) for a pass tier, or (0, 7, 100) for invalid/previous seasons.

    track: TRACK_BRAWL_PASS_PREMIUM (9) or TRACK_BRAWL_PASS_FREE (10).
    Invalid or previous seasons return 0 coins, item_id 7, box_id 100 (no animation).
    """
    season_key = str(season)
    pass_rewards = _load_pass_rewards()
    season_data = pass_rewards.get("seasons", {}).get(season_key, {})
    if not season_data:
        # Previous/invalid season → 0 coins, no animation
        return 0, 7, 100
    track_key = "premium" if track == TRACK_BRAWL_PASS_PREMIUM else "free"
    # PassRewards.json uses dict keyed by tier string, not list
    tier_data = season_data.get(track_key, {}).get(str(tier))
    if not tier_data:
        # Tier not found → 0 coins, no animation
        return 0, 7, 100
    amount = int(tier_data.get("quantity", 0) or 0)
    item_id = int(tier_data.get("object_id", 7) or 7)
    box_id = int(tier_data.get("box_id", 100) or 100)
    if box_id not in VALID_BOX_IDS:
        box_id = 100
    return amount, item_id, box_id


def _grant_zero(session, crypto, player, box_id=100):
    """Grant 0 coins and send a delivery packet with no reward."""
    from Classes.Logic.RewardDelivery import send_delivery
    send_delivery(
        session, crypto, player,
        [{"amount": 0, "reward_id": REWARD_COINS}],
        box_id=box_id,
        track_type=0,
        reward_rank=0,
        brawl_pass_season=0,
    )
    print(f"[517] granted 0 coins to account {getattr(player, 'LowID', '?')} (box_id={box_id})")


def _send_out_of_sync(session, crypto, player):
    """Send OutOfSyncMessage (24104) to the client."""
    Messaging.sendMessage(
        24104,
        {
            "Socket": getattr(session, "client", None),
            "Tick": 0,
            "ServerChecksum": 0,
            "ClientChecksum": 0,
        },
        crypto,
        player,
    )


class LogicClaimRankUpRewardCommand(LogicCommand):
    def __init__(self, commandData):
        super().__init__(commandData)

    def encode(self, fields):
        LogicCommand.encode(self, fields)
        return self.messagePayload

    def decode(self, calling_instance):
        fields = {}
        LogicCommand.decode(calling_instance, fields, False)
        names = ("a", "b", "g", "j", "bp", "p", "k", "id", "id2")
        for name in names:
            try:
                fields[name] = calling_instance.readVInt()
            except Exception:
                fields[name] = 0
                break
        return fields

    def execute(self, calling_instance, fields, cryptoInit):
        player = calling_instance.player
        database = getattr(player, "_db_dyn", None)
        if database is None:
            return

        # --- Executor risoltso solo dal database del chiamante ---
        low = int(getattr(player, "LowID", 0) or 0)
        if low <= 0:
            try:
                token = getattr(player, "Token", "")
                if token:
                    found = DynamicDB_find_lowid_by_token(token)
                    if found is not None:
                        low = int(found)
                        player.LowID = low
            except Exception:
                pass
        player.HighID = 0
        player.ID = [0, low]
        fields["ExecutorAccountID"] = [0, low]

        bp = int(fields.get("a", 0) or 0)        # track
        season = int(fields.get("g", 0) or 0)    # season
        tier = int(fields.get("j", 0) or 0)      # tier

        session = getattr(calling_instance, "session", None) or player.session
        crypto = getattr(session, "cryptoInit", None)
        if getattr(session, "client", None) is None:
            return

        # --- Controllo soglia già presa sul DB del chiamante ---
        # Check CanMultiTier flag (for admin tracking, doesn't block rewards)
        can_multi_tier = database.get_can_multi_tier() if database else False
        
        if bp == TRACK_TROPHY_ROAD_ID:
            already = int(database.get_trophy_road_claimed(season) or 0)
            if tier <= already:
                if can_multi_tier:
                    print(f"[517] trophy road tier {tier} gia' presa (CanMultiTier=true) -> concedo")
                else:
                    print(f"[517] trophy road tier {tier} gia' presa -> concedo comunque")
            amount, item_id, box_id = 1, REWARD_COINS, 100
            track_type = TRACK_TROPHY_ROAD
            reward_rank = tier + 1
            database.set_trophy_road_claimed(tier + 1, season)

        elif bp in (TRACK_BRAWL_PASS_PREMIUM, TRACK_BRAWL_PASS_FREE):
            premium = bp == TRACK_BRAWL_PASS_PREMIUM
            if not database.claim_brawl_pass_tier(premium, tier, season):
                if can_multi_tier:
                    print(f"[517] {'premium' if premium else 'free'} pass tier {tier} gia' presa (CanMultiTier=true) -> concedo")
                else:
                    print(f"[517] {'premium' if premium else 'free'} pass tier {tier} gia' presa -> concedo comunque")
            amount, item_id, box_id = _pass_reward(season, bp, tier)
            track_type = TRACK_BRAWL_PASS
            reward_rank = tier
        else:
            print(f"[517] unknown track bp={bp}, ignored")
            return

        # --- Concedi la ricompensa ---
        # For box_id 100: use JSON amount/item_id directly
        # For box_id 10/11/12: generate rewards from box_config
        if box_id != 100:
            rewards = generate_box_rewards(box_id)
            if not rewards:
                rewards = [{"amount": amount, "reward_id": item_id}]
        else:
            rewards = [{"amount": amount, "reward_id": item_id}]

        # grant all rewards
        for r in rewards:
            amt = int(r.get("amount", 0) or 0)
            rid = int(r.get("reward_id", REWARD_COINS) or 0)
            if rid == REWARD_COINS:
                player.Coins = int(getattr(player, "Coins", 0) or 0) + amt
                if database is not None and hasattr(database, "add_coins"):
                    database.add_coins(amt)
            elif rid == REWARD_GEMS:
                player.Gems = int(getattr(player, "Gems", 0) or 0) + amt
                if database is not None and hasattr(database, "add_gems"):
                    database.add_gems(amt)

        send_delivery(
            session, crypto, player, rewards,
            box_id=box_id,
            track_type=0,
            reward_rank=0,
            brawl_pass_season=0,
        )
        total_coins = sum(r.get("amount", 0) for r in rewards if r.get("reward_id") == REWARD_COINS)
        total_gems = sum(r.get("amount", 0) for r in rewards if r.get("reward_id") == REWARD_GEMS)
        print(f"[517] granted {total_coins} coins + {total_gems} gems to account {player.LowID} (box_id={box_id}, season={season}, tier={tier}, rewards={len(rewards)})")

    def getCommandType(self):
        return 517



def DynamicDB_find_lowid_by_token(token):
    from Classes.DB.DynamicDB import DynamicDB
    return DynamicDB.find_lowid_by_token(token)
