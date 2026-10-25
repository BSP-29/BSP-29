"""Minimal v29 battle bootstrap over one shared UDP socket.

This starts real client battles with a roster of Shelly bots and serves a
stationary initial world. Human movement inputs are reflected in subsequent
vision frames; the bots intentionally have no AI.
"""

import csv
import json
import math
import socket
import struct
import threading
import time
import traceback

import Configuration
from Classes.Logic import BrawlerLoadout
from Classes.Messaging import Messaging


_udp_socket = None
_udp_thread = None
_state_lock = threading.RLock()
_battles = {}
_sessions = {}
# Session ids seen on the UDP socket that match no live session, so a datagram
# that arrives but is discarded can be told apart from one that never arrives.
_unmatched_datagrams = {}
# Everything the UDP socket has seen, so "nothing arrived" can be told apart
# from "something arrived and was discarded". Lists because these are counters.
_datagrams_received = [0]
_short_datagrams = [0]
_map_cache = {}
_character_rows = None
_skill_rows = None
_skin_rows = None
_dynamic_tile_codes = None
_tile_rules_by_code = None
_tile_default_rule = None
_session_counter = 0
_bot_brawlers = (0,)  # Shelly


class _BitWriter:
    def __init__(self):
        self.data = bytearray()
        self.bit_offset = 0

    def bits(self, value, count):
        value = int(value)
        for bit in range(count):
            if self.bit_offset == 0:
                self.data.append(0)
            if (value >> bit) & 1:
                self.data[-1] |= 1 << self.bit_offset
            self.bit_offset = (self.bit_offset + 1) & 7

    def boolean(self, value):
        self.bits(1 if value else 0, 1)

    def signed(self, value, bits):
        self.bits(1 if value >= 0 else 0, 1)
        self.bits(abs(int(value)), bits)

    def positive_vint(self, value, length_bits):
        value = max(0, int(value))
        value_bits = max(1, value.bit_length())
        self.bits(value_bits - 1, length_bits)
        self.bits(value, value_bits)

    def positive_vint_often_zero(self, value, length_bits=3):
        if int(value) == 0:
            self.boolean(True)
        else:
            self.boolean(False)
            self.positive_vint(value, length_bits)

    def data_reference(self, class_id, instance_id):
        self.bits(class_id, 5)
        self.bits(instance_id, 8)

    def bytes(self):
        # The v29 server allocates the initial vision bitstream at 64 bytes.
        return bytes(self.data).ljust(max(64, len(self.data)), b"\0")


def _logic_rows(filename):
    path = f"Classes/Files/assets/csv_logic/{filename}"
    with open(path, "r", encoding="utf-8", newline="") as csv_file:
        reader = csv.reader(csv_file)
        header = next(reader, [])
        next(reader, None)  # The second CSV row contains field types.
        return [dict(zip(header, row)) for row in reader if row and row[0]]


def _to_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _to_bool(value):
    return str(value or "").strip().lower() == "true"


def _get_location(map_id):
    rows = _logic_rows("locations.csv")
    map_id = _to_int(map_id, -1)
    if map_id < 0 or map_id >= len(rows):
        return None
    return rows[map_id]


def _load_map(map_id):
    global _dynamic_tile_codes, _tile_rules_by_code, _tile_default_rule
    map_id = _to_int(map_id, -1)
    if map_id in _map_cache:
        return _map_cache[map_id]

    location = _get_location(map_id)
    if location is None:
        return None
    map_name = str(location.get("AllowedMaps", "")).split(",", 1)[0].strip()
    if not map_name:
        return None

    with open("Classes/Files/assets/tilemaps.json", "r", encoding="utf-8") as map_file:
        all_maps = json.load(map_file)
    raw_map = all_maps.get(map_name)
    if not raw_map:
        print(f"[Battle] Tilemap '{map_name}' not found for location {map_id}")
        return None

    width = _to_int(raw_map.get("WIDTH"))
    height = _to_int(raw_map.get("HEIGHT"))
    tile_data = str(raw_map.get("Data", ""))
    if width <= 0 or height <= 0 or len(tile_data) != width * height:
        print(f"[Battle] Invalid tilemap '{map_name}' ({width}x{height})")
        return None

    if _dynamic_tile_codes is None:
        codes = set()
        tile_rows = _logic_rows("tiles.csv")
        tile_rules = {}
        for row in tile_rows:
            code = str(row.get("TileCode", ""))[:1]
            if code:
                tile_rules.setdefault(code, row)
            if _to_bool(row.get("IsDestructible")) or _to_int(row.get("RespawnSeconds")) > 0:
                if code:
                    codes.add(code)
        _dynamic_tile_codes = codes
        _tile_rules_by_code = tile_rules
        _tile_default_rule = tile_rows[0] if tile_rows else {}

    points_1 = []
    points_2 = []
    points_all = []
    for y in range(height):
        for x in range(width):
            code = tile_data[y * width + x]
            point = (x * 300 + 150, y * 300 + 150)
            if code == "1":
                points_1.append(point)
                points_all.append(point)
            elif code == "2":
                points_2.append(point)
                points_all.append(point)

    mode = 1
    try:
        from Classes.Files.Classes.Locations import Locations
        mode = _to_int(Locations.getGamemodeVariation(map_id), 1)
    except Exception:
        pass

    result = {
        "id": map_id,
        "name": map_name,
        "mode": mode,
        "width": width,
        "height": height,
        "data": tile_data,
        "points1": points_1,
        "points2": points_2,
        "points_all": points_all,
        "dynamic_codes": _dynamic_tile_codes,
        "tile_rules": _tile_rules_by_code,
        "tile_default_rule": _tile_default_rule,
    }
    _map_cache[map_id] = result
    return result


def _load_character_rows():
    global _character_rows
    if _character_rows is None:
        _character_rows = _logic_rows("characters.csv")
    return _character_rows


def _load_skill_rows():
    global _skill_rows
    if _skill_rows is None:
        _skill_rows = _logic_rows("skills.csv")
    return _skill_rows


def _load_skin_rows():
    global _skin_rows
    if _skin_rows is None:
        _skin_rows = _logic_rows("skins.csv")
    return _skin_rows


def _skin_index_by_name(name):
    """The class 29 instance id for a skin name from characters.csv.

    characters.csv records DefaultSkin by name (BanditGirlDefault for Shelly),
    while the wire format wants the row index in skins.csv. Rows that are blank
    are skipped by _logic_rows and would shift the index, so the mapping is
    built from the same filtered list the encoder uses.
    """
    target = str(name or "").strip()
    if not target:
        return 0
    for index, row in enumerate(_load_skin_rows()):
        if str(row.get("Name", "")).strip() == target:
            return index
    return 0


def _default_skin_for_character(character):
    """The skin a character falls back to when the player has not picked one."""
    return _skin_index_by_name(character.get("DefaultSkin"))


def _selected_skin(player, brawler_id, character):
    """The player's own skin for this brawler, or the character's default.

    LogicSelectSkinCommand stores SelectedSkins[brawler] = skin instance id, so
    the client has already told us what it wants. Falling back to the default
    only matters for a player who never sent a selection.
    """
    try:
        selected = getattr(player, "SelectedSkins", None)
        if isinstance(selected, dict):
            skin = selected.get(brawler_id)
            if skin is None:
                skin = selected.get(str(brawler_id))
            skin = _to_int(skin, -1)
            if skin >= 0:
                return skin
    except Exception:
        pass
    return _default_skin_for_character(character)


def _get_character(brawler_id):
    rows = _load_character_rows()
    brawler_id = _to_int(brawler_id, 0)
    if 0 <= brawler_id < len(rows) and str(rows[brawler_id].get("Type", "")).lower() == "hero":
        return brawler_id, rows[brawler_id]
    return 0, rows[0]


def _skills_for_character(character):
    rows = _load_skill_rows()
    by_name = {str(row.get("Name", "")): (index, row) for index, row in enumerate(rows)}
    result = []
    for field in ("WeaponSkill", "UltimateSkill"):
        name = str(character.get(field, "") or "").strip()
        skill = by_name.get(name)
        if skill is None:
            continue
        index, row = skill
        max_charge = _to_int(row.get("MaxCharge"))
        result.append({
            "id": index,
            "max_charge": max_charge,
            "charge": max(1000, 1000 * max_charge),
            "can_change": _to_bool(row.get("SkillCanChange")),
        })
    return result


def _account_id(player):
    account = getattr(player, "ID", None)
    if isinstance(account, (list, tuple)) and len(account) >= 2:
        high, low = _to_int(account[0]), _to_int(account[1])
    else:
        high = _to_int(getattr(player, "HighID", 0))
        low = _to_int(getattr(player, "LowID", 0))
    return ((high & 0xFFFFFFFF) << 32) | (low & 0xFFFFFFFF)


def _player_level(player, is_bot):
    """Power level for this battle.

    Always Player.BrawlerLevel, with brawlers at id 100 or more held at 9. The
    previous per-brawler database lookup reported a different number than the
    lobby and the results screen, so health scaled differently from what the
    client was told.
    """
    if is_bot:
        return 0
    return BrawlerLoadout.resolve_power_level(
        player, getattr(player, "SelectedBrawler", 0)
    )


def _fallback_spawn(tile_map, team_index, index):
    points = tile_map["points1"] if team_index == 0 else tile_map["points2"]
    if not points:
        points = tile_map["points_all"]
    if points:
        return points[index % len(points)]
    return (tile_map["width"] * 150, tile_map["height"] * 150)


_GAME_MODE_VARIATIONS = {
    "CoinRush": 0,
    "AttackDefend": 2,
    "BossFight": 7,
    "BountyHunter": 3,
    "Artifact": 4,
    "LaserBall": 5,
    "BattleRoyale": 6,
    "BattleRoyaleTeam": 9,
    "Survival": 8,
    "Raid": 10,
    "RoboWars": 11,
    "Tutorial": 12,
    "Training": 13,
}


def _game_mode_variation(location):
    """Port GameModeUtil.GetGameModeVariation from v29.

    The reference derives the variation from Location.GameMode, not from the
    tilemap. Both were compared across every location that has a tilemap and
    they agree, so this is not a behaviour change today, but it keeps the
    source of truth where the reference puts it.
    """
    name = str((location or {}).get("GameMode") or "")
    return _GAME_MODE_VARIATIONS.get(name, -1)


def battle_player_slots(map_id=None):
    """How many players the mode of this location expects.

    Royale puts this in MatchMakingStatusMessage.Max. Sending the room size
    there instead tells the client the match is already full, which is a state
    it has no way to make sense of.
    """
    _index, location = _resolve_battle_location(map_id)
    variation = _game_mode_variation(location)
    if variation < 0:
        tile_map = _load_map(map_id if isinstance(map_id, int) else -1)
        variation = tile_map["mode"] if tile_map else 6
    return _players_required(variation)


def _players_required(mode):
    """Port GamePlayUtil.GetPlayerCountWithGameModeVariation from v29."""
    return {
        0: 6, 2: 6, 3: 6, 5: 6, 6: 10, 7: 6, 8: 3, 9: 10,
        10: 3, 11: 6, 12: 1, 13: 1, 14: 10, 15: 10, 16: 6,
        17: 6, 18: 3, 19: 6, 20: 6, 21: 6, 22: 6, 23: 6,
        24: 2, 25: 6, 26: 6, 27: 6,
    }.get(mode, 6)


def _make_roster(players, tile_map):
    mode = tile_map["mode"]
    player_count = _players_required(mode)
    has_two_teams = mode != 6
    roster = []
    team_counts = {}

    for player in players[:player_count]:
        index = len(roster)
        team = 0 if has_two_teams else index
        team_counts[team] = team_counts.get(team, 0) + 1
        brawler, character = _get_character(getattr(player, "SelectedBrawler", 0))
        spawn_team = team if has_two_teams else 0
        spawn_index = team_counts[team] - 1 if has_two_teams else index
        position = _fallback_spawn(tile_map, spawn_team, spawn_index)
        name_color = _to_int(getattr(player, "Namecolor", 0))
        roster.append({
            "player": player,
            "session": getattr(player, "session", None),
            "session_id": 0,
            "index": index,
            "team": team,
            "brawler": brawler,
            "skin": _selected_skin(player, brawler, character),
            "name": str(getattr(player, "Name", "Player") or "Player"),
            "account_id": _account_id(player),
            "thumbnail": 28000000 + _to_int(getattr(player, "Thumbnail", 0)),
            "name_color": 43000000 + name_color,
            "high_name_color": 0,
            "is_bot": False,
            "character": character,
            "level": _player_level(player, False),
            "skills": _skills_for_character(character),
            "position": position,
            "angle": 0,
            "state": 4,
            "attacking_ticks": 0,
            "fade_counter": 10,
            "pending_inputs": [],
            "movement_destination": None,
            "is_moving": False,
            "immunity_active": True,
            "immunity_ticks_remaining": 60,
            "object_id": 1000000 + index,
            "last_input": 0,
            "dudu": 0,
            "battle_tick": 0,
        })

    while len(roster) < player_count:
        index = len(roster)
        if not has_two_teams:
            team = index
        else:
            team = index % 2
            if team_counts.get(team, 0) >= 3:
                team = 1 - team
            if team_counts.get(team, 0) >= 3:
                # The reference swaps to the other side and adds the bot there
                # regardless, so the roster always reaches the count the mode
                # asks for. Stopping short would leave the roster smaller than
                # the number the client expects for this game mode.
                print(f"[Battle] mode {mode} wants {player_count} players but "
                      f"both sides already hold 3, adding bot {index} to "
                      f"team {team}")
        team_counts[team] = team_counts.get(team, 0) + 1
        brawler, character = _get_character(_bot_brawlers[0])
        spawn_team = team if has_two_teams else 0
        spawn_index = team_counts[team] - 1 if has_two_teams else index
        position = _fallback_spawn(tile_map, spawn_team, spawn_index)
        roster.append({
            "player": None,
            "session": None,
            "session_id": 0,
            "index": index,
            "team": team,
            "brawler": brawler,
            "skin": _default_skin_for_character(character),
            "name": "SHELLY",
            "account_id": 100000 + index,
            "thumbnail": 28000000,
            "name_color": 43000000,
            "high_name_color": 0,
            "is_bot": True,
            "character": character,
            "level": 0,
            "skills": _skills_for_character(character),
            "position": position,
            "angle": 0,
            "state": 4,
            "attacking_ticks": 0,
            "fade_counter": 10,
            "pending_inputs": [],
            "movement_destination": None,
            "is_moving": False,
            "immunity_active": True,
            "immunity_ticks_remaining": 60,
            "object_id": 1000000 + index,
            "last_input": 0,
            "dudu": 0,
            "battle_tick": 0,
        })
    return roster


def _make_initial_objects(roster, tile_map):
    """Build the initial GameObjectManager list used by the v29 vision frame."""
    objects = []
    for state in roster:
        objects.append({
            "kind": "character",
            "state": state,
            "object_index": state["index"],
            "data_class": 16,
            "data_instance": state["brawler"],
        })

    if tile_map["mode"] == 6:
        character_rows = _load_character_rows()
        lootbox = next(
            ((index, row) for index, row in enumerate(character_rows)
             if row.get("Name") == "LootBox"),
            None,
        )
        if lootbox is None:
            print("[Battle] v29 BattleRoyale character 'LootBox' is missing from characters.csv")
            return objects

        lootbox_instance, lootbox_character = lootbox
        random_seed = 0
        object_index = len(objects)
        # BattleMode uses LogicRandom(0), then one Rand(120) for each '4'
        # tile in row-major order, spawning a box when the result is < 60.
        for y in range(tile_map["height"]):
            for x in range(tile_map["width"]):
                if tile_map["data"][y * tile_map["width"] + x] != "4":
                    continue
                random_seed, roll = _logic_random(random_seed, 120)
                if roll >= 60:
                    continue

                state = {
                    "player": None,
                    "session": None,
                    "session_id": 0,
                    "index": 10 * 16,
                    "team": 0,
                    "brawler": lootbox_instance,
                    "name": "LootBox",
                    "account_id": 100000 + object_index,
                    "thumbnail": 28000000,
                    "name_color": 43000000,
                    "high_name_color": 0,
                    "is_bot": False,
                    "character": lootbox_character,
                    "level": 0,
                    "skills": _skills_for_character(lootbox_character),
                    "position": (x * 300 + 150, y * 300 + 150),
                    "angle": 0,
                    "state": 4,
                    "attacking_ticks": 0,
                    "fade_counter": 10,
                    "pending_inputs": [],
                    "movement_destination": None,
                    "is_moving": False,
                    "immunity_active": False,
                    "immunity_ticks_remaining": 0,
                    "object_id": 1000000 + object_index,
                    "last_input": 0,
                    "dudu": 0,
                    "battle_tick": 0,
                }
                objects.append({
                    "kind": "character",
                    "state": state,
                    "object_index": object_index,
                    "data_class": 16,
                    "data_instance": lootbox_instance,
                })
                object_index += 1
        return objects

    mode_item = {0: "OrbSpawner", 3: "Money"}.get(tile_map["mode"])
    if mode_item is not None:
        item_rows = _logic_rows("items.csv")
        item_instance = next(
            (index for index, row in enumerate(item_rows) if row.get("Name") == mode_item),
            None,
        )
        if item_instance is not None:
            object_index = len(objects)
            objects.append({
                "kind": "item",
                "name": mode_item,
                "object_index": object_index,
                "data_class": 18,
                "data_instance": item_instance,
                "position": (2950, 4950),
            })
        else:
            print(f"[Battle] v29 map object '{mode_item}' is missing from items.csv")

    return objects


def _logic_random(seed, max_value):
    """Return (next seed, result) with LogicRandom.Rand(int) semantics."""
    if max_value <= 0:
        return seed, 0
    if seed == 0:
        seed = -1

    def int32(value):
        value &= 0xFFFFFFFF
        return value if value < 0x80000000 else value - 0x100000000

    mixed = int32(seed ^ int32(seed << 13))
    mixed = int32(mixed ^ (mixed >> 17))
    next_seed = int32(mixed ^ int32(32 * mixed))
    value = next_seed
    if value < 0:
        value = -0x80000000 if value == -0x80000000 else -value
    return next_seed, value % max_value


def run_battle_simulation():
    """Whether to tick characters and stream vision frames.

    Set RunBattleSimulation=false in server.properties when every client plays
    locally as offline practice and never reads the UDP vision stream.
    """
    return bool(Configuration.settings.get("RunBattleSimulation", True))


def send_udp_info_with_loading():
    """Whether 24112 follows the loading screen without the client asking.

    On by default, against the reference. MessageManager ClientInfoReceived only
    answers 24112 in reply to a 10177, so Royale withholds it. Measured on the
    Android client, withholding it means the battle never starts at all: the
    client waits for the endpoint and never reaches the point where it would ask
    for one, so no 10177 ever arrives and no UDP socket is ever opened. Sending
    it unprompted is what gets the match going. Set it to false to compare.
    """
    return bool(Configuration.settings.get("SendUdpInfoWithLoading", True))


def resolve_client_address():
    """Whether UDPServerAddress is resolved to an IP before going to the client.

    On by default. Set it to false to put the raw configured value on the wire,
    hostname and all.
    """
    return bool(Configuration.settings.get("ResolveClientAddress", True))


def probe_client_udp():
    """Whether the server sends a UDP datagram to the client before waiting.

    On by default while the client is not opening with a packet of its own.
    """
    return bool(Configuration.settings.get("ProbeClientUdp", True))


def send_start_loading():
    """Whether 20559 is sent at all.

    Split from send_team_game_starting so the two battle packets can be tested
    one at a time. With only 20405 the client shows the ready state and does not
    stall, so the stall comes from one of these two, and the only way to tell
    which is to send them separately.
    """
    return bool(Configuration.settings.get("SendStartLoading", True))


def is_session_in_battle(session):
    """Whether this connection currently owns a battle session.

    Consulted by MessageManager before it sends the legacy 23457 lobby refresh.
    That refresh tells the client to go back to the lobby, so firing it while a
    match is starting bounces the client out of the battle instead of letting
    it start.
    """
    if session is None:
        return False
    with _state_lock:
        for state in _sessions.values():
            player_state = state.get("player") or {}
            if player_state.get("session") is session:
                return True
    return False


def _warn_stalled_sessions():
    """Warn once per session that never sent a datagram.

    Vision frames are only sent to a session whose endpoint is known, and the
    endpoint is only learned from its first datagram. A client that cannot reach
    the advertised UDP address therefore waits forever with no trace on the
    server, so say so out loud instead.
    """
    with _state_lock:
        for state in _sessions.values():
            if state.get("endpoint") is not None:
                continue
            # Age every loop and warn on the exact threshold, so it fires once.
            age = state.get("stallAge", 0) + 1
            state["stallAge"] = age
            if age != 20:
                continue
            received = _datagrams_received[0]
            if not received:
                print(
                    f"[UDP] NOTHING arrived on this socket in {age} listener "
                    f"loops. Not one datagram, from anyone. The advertised "
                    f"endpoint is not reachable, so this is the network, not the "
                    f"session id and not the advertisement."
                )
            else:
                print(
                    f"[UDP] {received} datagram(s) arrived, but none reached a "
                    f"live session: {_short_datagrams[0]} too short, "
                    f"{sum(_unmatched_datagrams.values())} with an unknown "
                    f"session id {sorted(_unmatched_datagrams)[:5]}. The client "
                    f"is talking to this server, so what it was told in 24112 is "
                    f"what needs checking."
                )
            print(
                f"[UDP] a session never sent a datagram after {age} listener "
                f"loops, so it gets no vision frames."
            )


def udp_info_fields(session, player_state, session_id):
    """Build the 24112 fields, in one place for both send paths.

    The default is the supplied layout: the session id goes in the first VInt
    and the address carries the port, so a client that parses host:port out of
    the string has everything it needs to open the socket.

    UdpInfoMode=reference swaps back to the v29 reference encoding, where the
    first field is the UDP port, the string is a bare IP, and the ten byte
    token is the session header the client echoes back, which is what
    _handle_datagram unpacks to find the session.
    """
    import struct

    mode = str(Configuration.settings.get("UdpInfoMode", "sessionfirst") or "sessionfirst")
    mode = mode.strip().lower()
    port = _to_int(Configuration.settings.get("UDPPort", 9339), 9339)
    advertised = get_udp_server_address(getattr(session, "address", None))
    session_id = int(session_id or 0)

    if mode in ("reference", "port", "royale"):
        return {
            "Socket": session.client,
            "Port": port,
            "BattleID": port,
            "Address": advertised,
            "ServerIP": advertised,
            "SessionID": session_id,
            "SessionFirst": False,
            "Token": struct.pack(">qH", session_id, 0),
            "Key": b"",
        }

    return {
        "Socket": session.client,
        "BattleID": session_id,
        "SessionID": session_id,
        "ServerIP": f"{advertised}:{port}" if advertised else "",
        "Address": f"{advertised}:{port}" if advertised else "",
        "SessionFirst": True,
        "Token": b"",
        "Key": b"",
    }


def send_team_game_starting():
    """Whether to send 24130 before the loading screen.

    Off. The only sender of 24130 in the v29 reference is Teams.StartGame, and
    its one call site is commented out in TeamSetMemberReadyReceived:

        member.IsReady = message.IsReady;
        team.TeamUpdated();

        //if (team.IsEveryoneReady())
        //{
        //    Teams.StartGame(team);
        //}

    So the reference never puts 24130 on the wire on its live path. Sending it
    anyway tells the client to start a game the server never asked it to start,
    which leaves the two sides out of step and stalls the match before the
    loading screen.
    """
    return bool(Configuration.settings.get("SendTeamGameStarting", False))


def _write_start_loading(player_state, battle):
    if not send_start_loading():
        print("[Battle] 20559 withheld, SendStartLoading is off")
        return

    players = []
    for state in battle["players"]:
        players.append({
            "AccountID": state["account_id"],
            "PlayerIndex": state["index"],
            "TeamIndex": state["team"],
            "Brawler": state["brawler"],
            "Skin": state["skin"],
            "Name": state["name"],
            "Thumbnail": state["thumbnail"],
            "NameColor": state["name_color"],
            "HighNameColor": state["high_name_color"],
        })

    session = player_state["session"]
    player = player_state["player"]
    location_id = int(battle["map"]["id"] or 0)
    location_global_id = 15 * 1000000 + location_id

    # 24130 is withheld. Its only sender in the reference is the dead
    # Teams.StartGame path, and putting it on the wire unsynchronises the
    # client, which stalls the match here.
    if send_team_game_starting():
        Messaging.sendMessage(
            24130,
            {
                "Socket": session.client,
                "LocationID": location_global_id,
            },
            session.cryptoInit,
            player,
        )

    # The original expression is kept deliberately. The canonical mapping from
    # BattleEndMessage disagrees with it, but the original is what was running
    # before and changing it is not free.
    game_mode = 6 if battle["map"]["mode"] == 6 else 1

    fields = {
        "Socket": session.client,
        "Players": players,
        "OwnIndex": player_state["index"],
        "TeamIndex": player_state["team"],
        "GameMode": game_mode,
        # StartLoadingMessage applies the class 15 prefix itself, so it needs
        # the bare location id, unlike 24130 above which takes the global id.
        "LocationID": location_id,
        "SpectateMode": 1 if _start_loading_spectate_mode() else 0,
    }
    # Printed because none of these appear anywhere else in the console, so a
    # change to them is otherwise invisible from the outside.
    print(f"[Battle] 20559 spectate={_start_loading_spectate_mode()} "
          f"mode={game_mode} roster={len(players)} own={player_state['index']} "
          f"team={player_state['team']} location={location_id}")
    Messaging.sendMessage(20559, fields, session.cryptoInit, player)

    # The reference only answers 24112 when the client asks with 10177, and the
    # one place it sends it unprompted is the spectate branch. Sending it early
    # hands the client an endpoint before it is in a state to use one.
    if send_udp_info_with_loading():
        info = udp_info_fields(session, player_state, player_state.get("session_id", 0))
        if info.get("Address"):
            Messaging.sendMessage(24112, info, session.cryptoInit, player)
        else:
            print("[Battle] no UDP server address resolved, client will have to ask")
    else:
        print("[Battle] 24112 withheld, waiting for the client to ask with 10177, "
              "which is what the reference does")

    # The reference client opens with a datagram of its own. None ever arrives
    # here, so the server makes the first move to the address and port the
    # client already proved it has on TCP.
    send_client_probe(session, player_state)


def _start_loading_spectate_mode():
    """Whether 20559 tells the client it is only watching.

    Off, because the v29 reference assigns this exactly once and only in the
    spectate branch. A client told it is spectating never takes control, never
    sends inputs and never asks for the UDP endpoint, so this one field decides
    whether the whole handshake happens at all.
    """
    return bool(Configuration.settings.get("SpectateMode", False))


def _dns_skip_name(data, offset):
    """Advance past a (possibly compressed) DNS name and return the new offset."""
    while offset < len(data):
        length = data[offset]
        if length == 0:
            return offset + 1
        if length & 0xC0 == 0xC0:
            # A compression pointer is always the last thing in a name.
            return offset + 2
        offset += 1 + length
    return offset


def _dns_query_a(hostname, resolver, timeout):
    """Ask one resolver for the A records of hostname. Returns a list of IPs.

    This deliberately does not use getaddrinfo. That goes through the OS stub
    resolver, which caches answers, so a dynamic name can still be served from a
    stale entry after the address has changed. Talking to a resolver over UDP on
    every ask is what makes the answer current.
    """
    try:
        labels = b"".join(
            bytes([len(part)]) + part.encode("ascii")
            for part in hostname.rstrip(".").split(".")
            if part
        )
    except (UnicodeError, ValueError):
        return []
    if not labels:
        return []

    # Standard query, recursion desired, exactly one question. The id varies per
    # call so a reply that is not the answer to this question can be spotted.
    transaction_id = time.monotonic_ns() & 0xFFFF
    packet = (
        struct.pack(">HHHHHH", transaction_id, 0x0100, 1, 0, 0, 0)
        + labels
        + b"\x00"
        + struct.pack(">HH", 1, 1)
    )

    family = socket.AF_INET6 if ":" in resolver else socket.AF_INET
    sock = socket.socket(family, socket.SOCK_DGRAM)
    try:
        sock.settimeout(timeout)
        sock.sendto(packet, (resolver, 53))
        data = sock.recv(2048)
    except (socket.timeout, OSError):
        return []
    finally:
        sock.close()

    if len(data) < 12:
        return []
    # recv accepts a datagram from any source, so confirm the reply is ours.
    if struct.unpack(">H", data[0:2])[0] != transaction_id:
        return []
    flags, _, answers = struct.unpack(">HHH", data[2:8])
    if not flags & 0x8000 or flags & 0x000F:
        # Not a response, or the server reported an error we cannot use.
        return []

    offset = _dns_skip_name(data, 12) + 4
    found = []
    for _ in range(answers):
        if offset >= len(data):
            break
        offset = _dns_skip_name(data, offset)
        if offset + 10 > len(data):
            break
        rtype, rclass, _, rdlength = struct.unpack(">HHIH", data[offset:offset + 10])
        offset += 10
        rdata = data[offset:offset + rdlength]
        offset += rdlength
        if rtype == 1 and rclass == 1 and rdlength == 4:
            found.append(socket.inet_ntoa(rdata))
    return found


def resolve_advertised_address(configured_address):
    """Resolve a configured hostname to a literal IP, or return it unchanged.

    The client is handed this string in 24112 and connects to it verbatim. Doing
    the lookup here means the device never has to, which matters on emulators and
    networks whose resolver will not answer for the domain.

    This holds no state and nothing is memoized, so a dynamic name is looked up
    again on every 24112 the server sends, and an address that changed while the
    server was running reaches the client without a restart. A failure is not
    fatal: the hostname is still a valid thing to put on the wire.
    """
    if not configured_address:
        return configured_address

    # An address literal needs no lookup at all.
    try:
        socket.inet_aton(configured_address)
        return configured_address
    except OSError:
        pass

    resolver = str(Configuration.settings.get("UdpDnsResolver", "") or "").strip()
    if resolver and resolver.lower() not in ("system", "default"):
        timeout = _to_int(Configuration.settings.get("UdpDnsTimeout", 1500), 1500) / 1000.0
        direct = _dns_query_a(configured_address, resolver, timeout)
        if direct:
            return _announce(configured_address, direct[0], "direct")
        print(f"[UDP] {resolver} gave no answer for {configured_address}; "
              f"falling back to the system resolver")

    try:
        infos = socket.getaddrinfo(configured_address, None, type=socket.SOCK_DGRAM)
    except (socket.gaierror, socket.herror, UnicodeError, OSError) as error:
        print(f"[UDP] could not resolve {configured_address} ({error}); "
              f"advertising the hostname unchanged")
        return configured_address

    candidates = []
    for info in infos:
        address = info[4][0] if len(info) > 4 and info[4] else None
        if not address:
            continue
        if address.startswith("::ffff:") or address == "::":
            continue
        candidates.append((info[0], address))

    # The shared listener is AF_INET, so an IPv6 literal can never be connected
    # to. Prefer IPv4 and only fall back to IPv6 if the name has nothing else.
    for wanted in (socket.AF_INET, socket.AF_INET6):
        for family, address in candidates:
            if family == wanted:
                return _announce(configured_address, address, "system")
    return _announce(configured_address, configured_address, "system")


def _announce(configured_address, address, source):
    if address == configured_address:
        print(f"[UDP] resolved {configured_address} -> {address} ({source}, "
              f"already a literal)")
        return configured_address
    print(f"[UDP] resolved {configured_address} -> {address} ({source})")
    return address


def get_udp_server_address(remote_address=None):
    """Return the address clients should use for the shared UDP listener."""
    configured_address = str(Configuration.settings.get("UDPServerAddress", "") or "").strip()
    if configured_address not in ("", "0.0.0.0", "::"):
        if resolve_client_address():
            return resolve_advertised_address(configured_address)
        return configured_address

    bind_host = str(Configuration.settings.get("UDPHost", "0.0.0.0") or "0.0.0.0").strip()
    if bind_host not in ("", "0.0.0.0", "::"):
        return bind_host

    remote_host = remote_address[0] if isinstance(remote_address, (list, tuple)) and remote_address else remote_address
    if remote_host:
        probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # UDP connect selects the outbound interface without sending a packet.
            probe.connect((str(remote_host), 9))
            return probe.getsockname()[0]
        except OSError:
            pass
        finally:
            probe.close()

    return ""


def _resolve_battle_location(requested=None):
    """Choose the location that goes into 20559 and 24130.

    The old default was index 1, which is Wanted3 and is flagged Disabled. A
    client asked for a location it does not have falls back to one of its own,
    which is why a Bounty battle came up as the default Heist map. Only 59 of
    the 296 locations are enabled, so this is worth being deliberate about.

    The location the client asked for always wins. It arrives through 14363
    (TeamSetLocationMessage) into room["mapID"], and through the last vint of
    14103 (MatchmakeRequestMessage). BattleLocation in server.properties is only
    the fallback for a client that has not chosen anything, so setting it can no
    longer override a player who picked a different mode. It accepts an index or
    a location name.
    """
    rows = _logic_rows("locations.csv")
    if not rows:
        return 4, None

    index = _to_int(requested, -1)

    if index < 0:
        configured = str(Configuration.settings.get("BattleLocation", "") or "").strip()
        if configured:
            if configured.lstrip("-").isdigit():
                index = _to_int(configured, -1)
            else:
                index = next(
                    (i for i, row in enumerate(rows)
                     if str(row.get("Name", "")).strip().lower() == configured.lower()),
                    -1,
                )
                if index < 0:
                    print(f"[Battle] BattleLocation '{configured}' matches no location "
                          f"name, falling back")
    if index < 0 or index >= len(rows):
        # Wanted6: enabled, BountyHunter, and its own tilemap.
        index = 4

    location = rows[index]
    if str(location.get("Disabled") or "").strip().lower() == "true":
        print(f"[Battle] location {index} ({location.get('Name')}) is flagged "
              f"Disabled in locations.csv. The client does not have it and will "
              f"show its own default map instead.")
    return index, location


def _start_battle(players, map_id, room_id=None):
    global _session_counter
    map_id, location = _resolve_battle_location(map_id)
    with _state_lock:
        if _udp_socket is None:
            print("[Battle] UDP listener is unavailable; battle start was skipped")
            return False
        tile_map = _load_map(map_id)
        if tile_map is None:
            print(f"[Battle] Cannot start: no valid map for location {map_id}")
            return False
        if location is not None:
            print(f"[Battle] location {map_id} = {location.get('Name')} "
                  f"({location.get('GameMode')}), tilemap "
                  f"{location.get('AllowedMaps')}")
        connected_players = [
            player for player in players
            if getattr(player, "session", None) is not None
            and hasattr(player.session, "client")
            and hasattr(player.session, "cryptoInit")
        ]
        if not connected_players:
            return False

        battle_key = room_id if room_id is not None else ("solo", id(connected_players[0]))
        if battle_key in _battles:
            return False
        roster = _make_roster(connected_players, tile_map)
        battle = {
            "room_id": room_id,
            "map": tile_map,
            "players": roster,
            "objects": _make_initial_objects(roster, tile_map),
            "tick": 0,
            "active": True,
            "started": False,
            "next_tick": None,
            "created": time.monotonic(),
        }

        for player_state in roster:
            if player_state["is_bot"]:
                continue
            # UDPSocket in the C# gateway assigns monotonically increasing
            # 64-bit session ids (SessionCounter++).
            _session_counter += 1
            session_id = _session_counter
            player_state["session_id"] = session_id
            player_state["session"].udp_session_id = session_id
            player_state["player"].battle_session_id = session_id
            _sessions[session_id] = {
                "battle": battle,
                "player": player_state,
                "endpoint": None,
                "vision_started": False,
            }
        _battles[battle_key] = battle
        if room_id is not None:
            room = _room_for_battle(room_id)
            if room is not None:
                room["battleStarted"] = True

    print(f"[Battle] Started location={map_id}, mode={tile_map['mode']}, roster={len(roster)}")
    for player_state in roster:
        if not player_state["is_bot"]:
            try:
                _write_start_loading(player_state, battle)
            except Exception:
                print("[Battle] Failed to send start-loading packets")
                print(traceback.format_exc())

    # The C# server starts BattleMode only after sending StartLoading to every
    # player. The first UDP datagram supplies its real remote endpoint later.
    with _state_lock:
        battle["started"] = True
        battle["next_tick"] = time.monotonic()
    return True


def start_team_battle(room_id):
    from Classes.TeamManager import get_room, get_room_players

    room = get_room(room_id)
    if room is None:
        return False
    # The map is whatever the room's owner last chose through 14363. It is
    # stored on the room, so every member of the team battles on the same
    # location. The fallback order matches _resolve_battle_location: the room
    # value first, then the server default handled there.
    players = get_room_players(room_id)
    map_id = _to_int(room.get("mapID"), -1)
    if map_id < 0:
        for p in players:
            if getattr(p, "session", None) is not None:
                selected = _to_int(getattr(p, "SelectedMap", 0), -1)
                if selected > 0:
                    map_id = selected
                    break
    return _start_battle(players, map_id, room_id)


def start_solo_battle(player, map_id=None):
    if map_id is None:
        # The client told us the location in 14103. SelectedMap is the same
        # value carried by 14363 and is used only when 14103 gave nothing.
        map_id = _to_int(getattr(player, "SelectedMap", 0), -1)
    return _start_battle([player], map_id)


def _room_for_battle(room_id):
    from Classes.TeamManager import get_room
    return get_room(room_id)


def remove_battle_session(player):
    session_id = _to_int(getattr(player, "battle_session_id", 0))
    if session_id <= 0:
        return None
    completed_room_id = None
    with _state_lock:
        state = _sessions.pop(session_id, None)
        # Counters from a finished match would misattribute traffic to the next
        # one, so start clean whenever the session table empties.
        if not _sessions:
            _unmatched_datagrams.clear()
            _datagrams_received[0] = 0
            _short_datagrams[0] = 0
        player.battle_session_id = 0
        session = getattr(player, "session", None)
        if session is not None:
            session.udp_session_id = 0
        if state is None:
            return None
        battle = state["battle"]
        if not any(other["battle"] is battle for other in _sessions.values()):
            battle["active"] = False
            for key, active_battle in list(_battles.items()):
                if active_battle is battle:
                    _battles.pop(key, None)
            completed_room_id = battle["room_id"]

    if completed_room_id is not None:
        room = _room_for_battle(completed_room_id)
        if room is not None:
            room["matchmakingStarted"] = False
            room.pop("battleStarted", None)
            previous_stats = room.pop("_matchmakingPreviousStats", {})
            from Classes.TeamManager import get_room_player
            for entry in room.get("players", []):
                player_id = _to_int(entry.get("plrID", 0))
                entry["STAT"] = previous_stats.get(player_id, 2)
                entry["READY"] = False
                member = get_room_player(completed_room_id, player_id)
                if member is not None:
                    member.isReady = False
    return completed_room_id


def _positive_vint(value):
    value = max(0, int(value))
    if value < 64:
        return bytes((value,))
    out = bytearray((value & 0x3F | 0x80,))
    value >>= 6
    while value > 0x7F:
        out.append(value & 0x7F | 0x80)
        value >>= 7
    out.append(value & 0x7F)
    return bytes(out)


class _BitReader:
    def __init__(self, data):
        self.data = data
        self.offset = 0

    def bits(self, count):
        value = 0
        for bit in range(count):
            byte_index = self.offset >> 3
            if byte_index >= len(self.data):
                raise ValueError("Truncated UDP input")
            bit_index = self.offset & 7
            value |= ((self.data[byte_index] >> bit_index) & 1) << bit
            self.offset += 1
        return value

    def signed(self, count):
        sign = 2 * self.bits(1) - 1
        return sign * self.bits(count)


def _read_vint(data, offset):
    if offset >= len(data):
        raise ValueError("Missing UDP message type")
    first = data[offset]
    offset += 1
    value = first & 0x3F
    if first & 0x40:
        value |= -64
        return value, offset
    shift = 6
    if first & 0x80:
        while offset < len(data):
            byte = data[offset]
            offset += 1
            value |= (byte & 0x7F) << shift
            shift += 7
            if not (byte & 0x80):
                break
    return value, offset


def _handle_inputs(state, payload):
    try:
        stream = _BitReader(payload)
        # Match ClientInputMessage.Decode: four header fields followed by a
        # five-bit input count and the ClientInput records.
        stream.bits(14)
        stream.bits(10)
        stream.bits(13)
        stream.bits(10)
        count = stream.bits(5)
        for _ in range(count):
            index = stream.bits(15)
            input_type = stream.bits(4)
            x = stream.signed(15)
            y = stream.signed(15)
            auto_attack = bool(stream.bits(1))
            emote_index = None
            if input_type == 9:
                emote_index = stream.bits(3)
            auto_attack_target = 0
            if auto_attack and stream.bits(1):
                auto_attack_target = stream.bits(14)
            state["pending_inputs"].append({
                "index": index,
                "type": input_type,
                "x": x,
                "y": y,
                "auto_attack": auto_attack,
                "auto_attack_target": auto_attack_target,
                "emote_index": emote_index,
            })
    except (ValueError, IndexError):
        return


def _apply_pending_inputs(battle):
    """Drain UDP inputs at the start of a BattleMode tick, in receive order."""
    for state in battle["players"]:
        pending = state["pending_inputs"]
        state["pending_inputs"] = []
        for input_data in pending:
            if input_data["index"] <= state["last_input"]:
                continue
            state["last_input"] = input_data["index"]
            if input_data["type"] != 2:
                continue

            # This server intentionally keeps its Shelly bots stationary. For
            # human movement, preserve the existing lightweight position
            # update while applying it at the same tick boundary as C#.
            tile_map = battle["map"]
            max_x = tile_map["width"] * 300
            max_y = tile_map["height"] * 300
            x, y = input_data["x"], input_data["y"]
            old_x, old_y = state["position"]
            dx, dy = x - old_x, y - old_y
            if dx or dy:
                state["angle"] = int(math.degrees(math.atan2(dy, dx))) % 360
            state["position"] = (max(0, min(max_x, x)), max(0, min(max_y, y)))


def _tick_character(state, battle):
    """Advance the static Character fields that affect the encoded vision."""
    # HandleMoveAndAttack sets this to 63 whenever no skill is active. The
    # static battle bootstrap never activates skills, matching idle C# bots.
    state["attacking_ticks"] = 63

    # C# starts ticking the 60-tick immunity only after the 120-tick intro.
    if battle["tick"] > 120 and state["immunity_active"]:
        state["immunity_ticks_remaining"] -= 1
        if state["immunity_ticks_remaining"] <= 0:
            state["immunity_active"] = False

    tile_map = battle["map"]
    x, y = state["position"]
    tile_x = max(0, min(tile_map["width"] - 1, x // 300))
    tile_y = max(0, min(tile_map["height"] - 1, y // 300))
    code = tile_map["data"][tile_y * tile_map["width"] + tile_x]
    tile_rule = tile_map["tile_rules"].get(code, tile_map["tile_default_rule"])
    if _to_bool(tile_rule.get("HidesHero")):
        state["fade_counter"] = max(0, state["fade_counter"] - 1)
    else:
        state["fade_counter"] = min(10, state["fade_counter"] + 1)


def _write_character(bit_stream, state, own_object_id, viewer_team):
    character = state["character"]
    x, y = state["position"]
    # Character.Encode receives isOwnObject by comparing the GameObject's
    # GlobalId, not the player index.
    own_object = state["object_id"] == own_object_id
    index = state["index"] + 16 * state["team"]
    speed = _to_int(character.get("Speed"))
    auto_attack = _to_int(character.get("AutoAttackDamage")) > 0
    char_type = str(character.get("Type", ""))
    max_hp_base = _to_int(character.get("Hitpoints"), 3800)
    level = state["level"]
    max_hp = max_hp_base + int(max_hp_base * 0.05) * level
    hitpoints = max_hp

    bit_stream.positive_vint(x, 4)
    bit_stream.positive_vint(y, 4)
    bit_stream.positive_vint(index, 3)
    bit_stream.positive_vint(0, 4)
    fade_counter = 10 if viewer_team == index // 16 else state.get("fade_counter", 10)
    bit_stream.bits(fade_counter, 4)

    if auto_attack or speed != 0 or char_type == "Minion_Building_charges_ulti":
        if own_object:
            bit_stream.boolean(False)
            bit_stream.boolean(False)
        else:
            bit_stream.bits(state["angle"] % 512, 9)
            bit_stream.bits(state["angle"] % 512, 9)
        bit_stream.bits(state["state"], 3)
        bit_stream.boolean(False)
        bit_stream.signed(state["attacking_ticks"], 6)
        bit_stream.boolean(False)
        bit_stream.boolean(False)
        bit_stream.boolean(False)
        bit_stream.boolean(False)
    else:
        bit_stream.bits(state["state"], 3)

    bit_stream.positive_vint_often_zero(0)
    bit_stream.positive_vint_often_zero(0)
    bit_stream.boolean(False)
    bit_stream.boolean(False)
    bit_stream.bits(0, 2)  # poison type

    if max_hp_base > 5799 or state["battle"]["map"]["mode"] == 6:
        bit_stream.positive_vint(hitpoints, 4)
        bit_stream.positive_vint(max_hp, 4)
    else:
        bit_stream.bits(hitpoints, 13)
        bit_stream.bits(max_hp, 13)

    if str(character.get("Type", "")).lower() == "hero":
        bit_stream.positive_vint_often_zero(0)
        bit_stream.positive_vint_often_zero(0)
        bit_stream.boolean(False)
        bit_stream.boolean(True)
        bit_stream.boolean(False)
        bit_stream.boolean(state["immunity_active"])
        bit_stream.boolean(False)
        bit_stream.boolean(False)
        bit_stream.boolean(False)
        bit_stream.boolean(False)
        bit_stream.boolean(False)
        bit_stream.boolean(False)
        if own_object:
            bit_stream.boolean(False)
            bit_stream.bits(0, 4)

    bit_stream.bits(0, 2)
    bit_stream.boolean(False)
    bit_stream.bits(0, 9)
    if own_object:
        bit_stream.boolean(False)
        bit_stream.boolean(False)
    bit_stream.bits(0, 5)  # no damage indicators

    for skill in state["skills"]:
        bit_stream.positive_vint_often_zero(0)
        bit_stream.boolean(False)
        bit_stream.positive_vint_often_zero(0)
        if skill["max_charge"] >= 1:
            bit_stream.bits(skill["charge"], 12)
        if skill["can_change"]:
            bit_stream.bits(skill["id"], 8)


def _write_item(bit_stream, item):
    """Encode the v29 Item object layout used by OrbSpawner and Money."""
    x, y = item["position"]
    bit_stream.positive_vint(x, 4)
    bit_stream.positive_vint(y, 4)
    bit_stream.positive_vint(0, 3)  # GameObject index
    bit_stream.positive_vint(0, 4)  # Z
    bit_stream.bits(10, 4)  # initial GameObject fade counter
    if item["name"] == "OrbSpawner":
        bit_stream.bits(0, 14)
        bit_stream.bits(0, 14)


def _encode_vision(battle, player_state):
    bit_stream = _BitWriter()
    own_object_id = player_state["object_id"]
    own_index = player_state["index"]
    own_team = player_state["team"]
    tile_map = battle["map"]

    bit_stream.bits(own_object_id, 21)
    if tile_map["mode"] == 0:
        bit_stream.positive_vint(0, 4)
    bit_stream.boolean(False)
    bit_stream.signed(-1, 4)
    bit_stream.boolean(True)
    bit_stream.boolean(True)
    bit_stream.boolean(True)
    bit_stream.boolean(False)
    if tile_map["width"] < 22:
        bit_stream.bits(0, 5)
        bit_stream.bits(0, 6)
        bit_stream.bits(tile_map["width"] - 1, 5)
    else:
        bit_stream.bits(0, 6)
        bit_stream.bits(0, 6)
        bit_stream.bits(tile_map["width"] - 1, 6)
    bit_stream.bits(tile_map["height"] - 1, 6)

    for x in range(tile_map["width"]):
        for y in range(tile_map["height"]):
            code = tile_map["data"][y * tile_map["width"] + x]
            if code in tile_map["dynamic_codes"]:
                bit_stream.boolean(False)

    bit_stream.bits(1, 1)
    for state in battle["players"]:
        bit_stream.bits(0, 1)
        bit_stream.boolean(False)  # no player has an ultimate charged
        if tile_map["mode"] == 6:
            bit_stream.bits(0, 4)
        if state["index"] == own_index:
            bit_stream.bits(0, 12)
            bit_stream.bits(0, 1)
            bit_stream.bits(0, 1)

    bit_stream.bits(1, 1)
    if tile_map["mode"] == 6:
        bit_stream.bits(len(battle["players"]), 4)
    for _state in battle["players"]:
        if tile_map["mode"] != 6:
            bit_stream.boolean(True)
            bit_stream.positive_vint(0, 3)
        else:
            bit_stream.boolean(False)
        bit_stream.boolean(False)  # empty kill list

    objects = []
    for game_object in battle["objects"]:
        if game_object["kind"] == "character":
            object_state = game_object["state"]
            object_index = object_state["index"] + 16 * object_state["team"]
            visible = object_state["fade_counter"] > 0 or object_index // 16 == own_team
        else:
            # GameObject.Index defaults to zero and Items start forced visible.
            visible = True
        if visible:
            objects.append(game_object)
    bit_stream.bits(len(objects), 8)
    for game_object in objects:
        bit_stream.data_reference(game_object["data_class"], game_object["data_instance"])
    for game_object in objects:
        bit_stream.bits(game_object["object_index"], 14)
    for game_object in objects:
        if game_object["kind"] == "character":
            state = game_object["state"]
            state["battle"] = battle
            _write_character(bit_stream, state, own_object_id, own_team)
        else:
            _write_item(bit_stream, game_object)
    bit_stream.bits(0, 8)

    vision = bit_stream.bytes()
    from Classes.ByteStream import ByteStream
    message = ByteStream(b"")
    message.writeVInt(battle["tick"])
    message.writeVInt(player_state["last_input"])
    message.writeVInt(0)
    message.writeVInt(0)  # viewers
    message.writeBoolean(False)
    message.writeInt(len(vision))
    message.messagePayload += vision
    return message.messagePayload


def send_client_probe(session, player_state):
    """Make the first move over UDP instead of waiting for the client.

    The reference client opens by sending. Nothing has ever arrived here, so it
    is not. A NAT also holds no mapping for the client until the client sends
    something over UDP, so on a normal home router this cannot open the
    conversation on its own. Sending anyway to the address and port the client
    is known to hold on TCP answers a question no server side log can: does
    anything get through from this machine to that device.

    If the client answers, its real UDP endpoint is learned from the reply and
    the battle runs normally from then on.
    """
    if not probe_client_udp():
        return False
    address = getattr(session, "address", None)
    sock = _udp_socket
    if sock is None or not address:
        return False
    try:
        payload = _encode_vision_probe()
        packet = (
            struct.pack(">QH", player_state["session_id"], 0)
            + _positive_vint(24109)
            + _positive_vint(len(payload))
            + payload
        )
        sock.sendto(packet, (address[0], address[1]))
        print(f"[UDP] probed the client at {address[0]}:{address[1]} with "
              f"{len(packet)} bytes. A reply here would prove the path is open "
              f"and give us the real UDP port.")
        return True
    except OSError as error:
        print(f"[UDP] probe to {address[0]}:{address[1]} failed: {error}")
        return False


def _encode_vision_probe():
    """A VisionUpdate body carrying no vision data, just the fixed fields.

    Same shape as _encode_vision so a client that accepts one accepts this.
    """
    from Classes.ByteStream import ByteStream
    message = ByteStream(b"")
    message.writeVInt(0)   # Tick
    message.writeVInt(0)   # HandledInputs
    message.writeVInt(0)   # unknown
    message.writeVInt(0)   # Viewers
    message.writeBoolean(False)
    message.writeInt(0)    # no vision data
    return message.messagePayload


def _send_vision(state):
    sock = _udp_socket
    endpoint = state.get("endpoint")
    if sock is None or endpoint is None or not state["battle"].get("started"):
        return False
    battle = state["battle"]
    player_state = state["player"]
    try:
        payload = _encode_vision(battle, player_state)
        packet = (
            struct.pack(">QH", player_state["session_id"], 0)
            + _positive_vint(24109)
            + _positive_vint(len(payload))
            + payload
        )
        sock.sendto(packet, endpoint)
        if not state.get("vision_started", False):
            state["vision_started"] = True
            print(f"[UDP] First VisionUpdate sent for session {player_state['session_id']}")
        return True
    except OSError as error:
        print(f"[UDP] VisionUpdate send failed: {error}")
        return False
    except Exception:
        print("[Battle] Failed to encode/send UDP vision update")
        print(traceback.format_exc())
        return False


def _handle_datagram(data, endpoint):
    with _state_lock:
        _datagrams_received[0] += 1
    if len(data) < 10:
        with _state_lock:
            _short_datagrams[0] += 1
            first = _short_datagrams[0] == 1
        if first:
            print(f"[UDP] datagram of {len(data)} bytes from "
                  f"{endpoint[0]}:{endpoint[1]} is too short to carry a session "
                  f"id, discarded. Expected at least 10.")
        return
    # This is UDPSocket.ReceiveCallback's framing: an 8-byte session id and
    # an ignored 2-byte field, followed by one type/length/payload message.
    session_id, _flags = struct.unpack(">QH", data[:10])
    with _state_lock:
        state = _sessions.get(session_id)
        if state is None:
            _unmatched_datagrams[session_id] = _unmatched_datagrams.get(session_id, 0) + 1
            seen = len(_unmatched_datagrams)
            total = sum(_unmatched_datagrams.values())
            first = ""
            if seen <= 5:
                first = f" ids seen so far: {sorted(_unmatched_datagrams)}"
            print(f"[UDP] datagram for unknown session {session_id} from "
                  f"{endpoint[0]}:{endpoint[1]}, discarded ({total} so far).{first}")
            return
        first_datagram = state.get("endpoint") is None
        if first_datagram:
            state["endpoint"] = endpoint
    if first_datagram:
        print(f"[UDP] First datagram for session {session_id} from {endpoint[0]}:{endpoint[1]}")
    try:
        if len(data) > 10:
            message_type, offset = _read_vint(data, 10)
            length, offset = _read_vint(data, offset)
            if length < 0 or offset + length > len(data):
                raise ValueError("Truncated UDP message payload")
            payload = data[offset:offset + length]
            if message_type == 10555:
                _handle_inputs(state["player"], payload)
    except (ValueError, IndexError):
        # Any datagram carries a usable source endpoint; no application
        # handshake is required. Keep the endpoint and continue the battle tick.
        pass
def _run_udp_listener():
    while True:
        try:
            data, endpoint = _udp_socket.recvfrom(4096)
            _handle_datagram(data, endpoint)
        except socket.timeout:
            pass
        except OSError as error:
            print(f"[UDP] Listener stopped: {error}")
            return
        except Exception:
            print("[UDP] Ignored malformed datagram")
            print(traceback.format_exc())

        now = time.monotonic()

        _warn_stalled_sessions()

        # On a patched client that plays matches locally as offline practice,
        # nobody consumes the vision frames. Ticking every character at 20 Hz
        # for them is pure cost, so it can be switched off in server.properties.
        # This must skip the tick only: returning here would kill the listener
        # thread and stop accepting datagrams for the rest of the process.
        if run_battle_simulation():
            _tick_battles(now)


def _tick_battles(now):
    with _state_lock:
        battles = list(_battles.values())
    for battle in battles:
        with _state_lock:
            if not battle.get("active") or not battle.get("started"):
                continue
            next_tick = battle.get("next_tick")
            if next_tick is None or now < next_tick:
                continue

            # C# BattleMode handles queued input, runs object PreTick/Tick,
            # advances game time, then serializes VisionUpdate.
            _apply_pending_inputs(battle)
            for game_object in battle["objects"]:
                if game_object["kind"] == "character":
                    _tick_character(game_object["state"], battle)
            battle["tick"] += 1
            # Keep an independent 20 Hz clock for each battle, beginning
            # with the immediate first callback of BattleMode.Start().
            battle["next_tick"] = now + 0.05
            player_states = [
                state for state in _sessions.values()
                if state["battle"] is battle and state.get("endpoint") is not None
            ]
        for state in player_states:
            _send_vision(state)


def start_udp_listener():
    global _udp_socket, _udp_thread
    with _state_lock:
        if _udp_socket is not None:
            return True
        host = str(Configuration.settings.get("UDPHost", "0.0.0.0"))
        port = _to_int(Configuration.settings.get("UDPPort", 9339), 9339)
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.bind((host, port))
        except OSError as error:
            sock.close()
            print(f"[UDP] Could not bind {host}:{port}: {error}")
            print("[UDP] Battles are DISABLED: _start_battle refuses to run without "
                  "this socket, so every match start will be skipped.")
            print("[UDP] Fix: change UDPPort in server.properties, or close whatever "
                  "already holds the port.")
            return False
        sock.settimeout(0.01)
        _udp_socket = sock
        _udp_thread = threading.Thread(target=_run_udp_listener, name="battle-udp", daemon=True)
        _udp_thread.start()
        advertised = str(Configuration.settings.get("UDPServerAddress", "") or "").strip()
        print(f"[UDP] Shared battle listener started at {host}:{port}")
        if advertised and advertised not in ("0.0.0.0", "::", ""):
            on_wire = resolve_advertised_address(advertised) if resolve_client_address() else advertised
            print(f"[UDP] Clients are told to reach battles at {on_wire}:{port} "
                  f"in 24112. If that address is not this machine, vision frames "
                  f"will go to the wrong host. UDP forwarding must also be open on "
                  f"the router; no setting here can change that.")
        else:
            print("[UDP] UDPServerAddress is unset, clients get the socket's own "
                  "address. Set it in server.properties if you are behind NAT.")
        return True
