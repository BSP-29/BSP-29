"""Effective power level and gear for a brawler.

Single source of truth so the team lobby, the loading screen, the running battle
and the results screen cannot report different numbers for the same player.

Rules:
  - the level is always Player.BrawlerLevel
  - a brawler whose id is 100 or more is held at level 9
  - a member is always reported with their brawler's star power and gadget, so
    gear is maxed rather than left empty

There is no separate friendly battle mode: it is played exactly like a normal
one, so nothing branches on the game mode here.

TeamBPL is deliberately not consulted. It was hardcoded to 10 and shadowed
BrawlerLevel everywhere, so the lobby always advertised level 10.
"""
import csv
import os

MAX_POWER_LEVEL = 10
SUPPRESSED_POWER_LEVEL = 9
SUPPRESSED_BRAWLER_ID = 100

_CARDS_CSV = os.path.join("Classes", "Files", "assets", "csv_logic", "cards.csv")
_CHARACTERS_CSV = os.path.join("Classes", "Files", "assets", "csv_logic", "characters.csv")

CARD_TYPE_STARPOWER = "4"
CARD_TYPE_GADGET = "5"

_GEAR_INDEX = None


def _to_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def resolve_power_level(player, brawler_id):
    """Power level to report for this brawler."""
    if _to_int(brawler_id) >= SUPPRESSED_BRAWLER_ID:
        return SUPPRESSED_POWER_LEVEL
    return _to_int(getattr(player, "BrawlerLevel", 0))


def _database_int(database, method_name):
    method = getattr(database, method_name, None)
    if callable(method):
        try:
            return _to_int(method())
        except Exception:
            return 0
    return 0


def _brawler_ids_by_name():
    index = {}
    try:
        with open(_CHARACTERS_CSV, newline="", encoding="utf-8") as handle:
            for position, row in enumerate(csv.reader(handle)):
                # The first two rows are headers, so the id is position - 2.
                if position < 2 or not row:
                    continue
                index[row[0]] = position - 2
    except OSError:
        return {}
    return index


def gear_index():
    """brawler id -> (star power card id, gadget card id), parsed once.

    Cards.getBrawlerStarpowers reopens both csv files per call and prints every
    row it walks, so it cannot be used on a path that runs per member per
    TeamMessage.
    """
    global _GEAR_INDEX
    if _GEAR_INDEX is not None:
        return _GEAR_INDEX

    names = _brawler_ids_by_name()
    index = {}
    try:
        with open(_CARDS_CSV, newline="", encoding="utf-8") as handle:
            for position, row in enumerate(csv.reader(handle)):
                if position < 2 or len(row) < 7:
                    continue
                if row[6] not in (CARD_TYPE_STARPOWER, CARD_TYPE_GADGET):
                    continue
                brawler_id = names.get(row[3])
                if brawler_id is None:
                    continue

                star_power, gadget = index.get(brawler_id, (0, 0))
                if row[6] == CARD_TYPE_STARPOWER:
                    if not star_power and row[4].lower() != "true":
                        star_power = position - 2
                elif not gadget:
                    gadget = position - 2
                index[brawler_id] = (star_power, gadget)
    except OSError:
        index = {}

    _GEAR_INDEX = index
    return index


def resolve_gear(player, brawler_id):
    """Return the (star power card id, gadget card id) to advertise.

    Gear is always maxed: whatever the player has equipped wins, and anything
    missing is filled from that brawler's own star power and gadget. Both are
    class 23 references, and an unset global id collapses to a single zero VInt
    on the wire rather than a class/instance pair.
    """
    database = getattr(player, "_db_dyn", None)
    star_power = _database_int(database, "get_equipped_star_power")
    gadget = _database_int(database, "get_equipped_gadget")

    available_star_power, available_gadget = gear_index().get(_to_int(brawler_id), (0, 0))
    if not star_power:
        star_power = available_star_power
    if not gadget:
        gadget = available_gadget

    return star_power, gadget