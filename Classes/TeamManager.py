# Room and player records follow the v28 Utils.G.Gameroom schema.
Teams = []

# Keep runtime Player objects outside the room records so their shape stays v28-compatible.
_room_players = {}
_room_high_ids = {}


def _as_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _database_for_player(player):
    database = getattr(player, "_db_dyn", None) if player is not None else None
    if database is None:
        from Classes.DB.DynamicDB import DynamicDB
        player_id = _as_int(getattr(player, "LowID", 0)) if player is not None else 0
        database = DynamicDB(player_id=str(player_id))
    return database


def _find_room(room_id):
    room_id = _as_int(room_id)
    for room in Teams:
        if _as_int(room.get("id")) == room_id:
            return room
    return None


def get_room(room_id):
    return _find_room(room_id)


def get_member_record(room_id, player_id):
    room = _find_room(room_id)
    if room is None:
        return None
    player_id = _as_int(player_id)
    for entry in room.get("players", []):
        if _as_int(entry.get("plrID")) == player_id:
            return entry
    return None


def get_room_player(room_id, player_id):
    room_id = _as_int(room_id)
    player_id = _as_int(player_id)
    return _room_players.get(room_id, {}).get(player_id)


def _sync_member_record(room_id, entry):
    member = get_room_player(room_id, entry.get("plrID"))
    if member is not None:
        entry["NAME"] = str(getattr(member, "Name", entry.get("NAME", "")))
        entry["READY"] = bool(getattr(member, "isReady", entry.get("READY", False)))
    return member


def get_room_players(room_id):
    room = _find_room(room_id)
    if room is None:
        return []
    players = []
    for entry in room.get("players", []):
        member = _sync_member_record(room_id, entry)
        if member is not None:
            players.append(member)
    return players


def _make_player_entry(player_id, name, owner=False, status=2):
    return {
        "plrID": _as_int(player_id),
        "STAT": _as_int(status, 2),
        "READY": False,
        "NAME": str(name or ""),
        "OWNER": bool(owner),
    }


def _owner_entry(room):
    for entry in room.get("players", []):
        if bool(entry.get("OWNER")):
            return entry
    if room.get("players"):
        room["players"][0]["OWNER"] = True
        return room["players"][0]
    return None


def _set_player_membership(player, room, owner_id):
    room_id = _as_int(room.get("id"))
    player_id = _as_int(getattr(player, "LowID", 0))
    room_high = _room_high_ids.get(room_id, 0)
    is_owner = player_id == _as_int(owner_id)
    player.TeamID = [room_high, room_id]
    player.TeamType = _as_int(room.get("roomType"))
    player.TeamOwnerID = _as_int(owner_id)
    player.TeamIsOwner = is_owner
    # The old default was index 1 (Wanted3, disabled). Index 4 (Wanted6) is
    # the enabled BountyHunter location that the client actually has.
    player.TeamMapID = _as_int(room.get("mapID", 4))
    _database_for_player(player).set_team_membership(
        room_id,
        player.TeamType,
        player.TeamOwnerID,
        is_owner,
        player.TeamMapID,
        room_high,
    )


def _persist_room(room):
    room_id = _as_int(room.get("id"))
    owner = _owner_entry(room)
    if owner is None:
        return
    owner_id = _as_int(owner.get("plrID"))

    for entry in room.get("players", []):
        player_id = _as_int(entry.get("plrID"))
        member = get_room_player(room_id, player_id)
        if member is not None:
            _set_player_membership(member, room, owner_id)
            entry["NAME"] = str(getattr(member, "Name", entry.get("NAME", "")))
            continue

        from Classes.DB.DynamicDB import DynamicDB
        DynamicDB(player_id=str(player_id)).set_team_membership(
            room_id,
            _as_int(room.get("roomType")),
            owner_id,
            player_id == owner_id,
            # Default to 122 (Gemgrab19 / CoinRush, enabled) when the client's
            # selection is not in the room data. The old default (1 = Wanted3)
            # is disabled and does not match its tilemap.
            _as_int(room.get("mapID", 122)),
            _room_high_ids.get(room_id, 0),
        )


def _restore_room_from_database(room_id, database, requested_owner_id=0, joining_player=None):
    room_id = _as_int(room_id)
    existing = _find_room(room_id)
    if existing is not None:
        return existing

    persisted_members = database.get_team_members(room_id)
    if not persisted_members:
        return None

    owner_id = _as_int(requested_owner_id)
    if owner_id <= 0:
        owners = [member for member in persisted_members if member["TeamIsOwner"]]
        if owners:
            owner_id = owners[0]["player_id"]
        else:
            known_owner_ids = [member["TeamOwnerID"] for member in persisted_members if member["TeamOwnerID"] > 0]
            owner_id = known_owner_ids[0] if known_owner_ids else persisted_members[0]["player_id"]

    persisted_members = [
        member for member in persisted_members
        if member["TeamOwnerID"] in (0, owner_id) or member["player_id"] == owner_id
    ]
    if joining_player is not None:
        joining_id = _as_int(getattr(joining_player, "LowID", 0))
        if not any(member["player_id"] == joining_id for member in persisted_members):
            membership = _database_for_player(joining_player).get_team_membership()
            persisted_members.append({
                "player_id": joining_id,
                "TeamID": membership["TeamID"],
                "TeamType": membership["TeamType"],
                "TeamOwnerID": owner_id,
                "TeamIsOwner": joining_id == owner_id,
                "TeamMapID": membership["TeamMapID"],
                "Name": getattr(joining_player, "Name", ""),
            })

    owner_data = next(
        (member for member in persisted_members if member["player_id"] == owner_id),
        persisted_members[0],
    )
    room_type = owner_data["TeamType"]
    map_id = owner_data["TeamMapID"]
    if map_id == 0:
        map_id = 1

    room_players = []
    for member in sorted(persisted_members, key=lambda item: (item["player_id"] != owner_id, item["player_id"])):
        room_players.append(_make_player_entry(
            member["player_id"],
            member["Name"],
            owner=member["player_id"] == owner_id,
            status=2,
        ))

    room = {
        "id": room_id,
        "mapID": map_id,
        "roomType": room_type,
        "Tick": 1,
        "premade": [],
        "msg": [],
        "invites": [],
        "players": room_players,
    }
    Teams.append(room)
    _room_players.setdefault(room_id, {})
    _room_high_ids[room_id] = owner_data["TeamID"][0]
    return room


def restore_player_team(player):
    database = _database_for_player(player)
    membership = database.get_team_membership()
    room_high, room_id = membership["TeamID"]
    if room_id <= 0:
        player.TeamID = [0, 0]
        player.TeamType = 0
        player.TeamOwnerID = 0
        player.TeamIsOwner = False
        player.TeamMapID = 1
        return None

    owner_id = membership["TeamOwnerID"]
    if owner_id <= 0 and membership["TeamIsOwner"]:
        owner_id = _as_int(getattr(player, "LowID", 0))

    room = _restore_room_from_database(room_id, database, owner_id, player)
    if room is None:
        database.clear_team_membership()
        player.TeamID = [0, 0]
        player.TeamType = 0
        player.TeamOwnerID = 0
        player.TeamIsOwner = False
        player.TeamMapID = 1
        return None

    player_id = _as_int(getattr(player, "LowID", 0))
    entry = get_member_record(room_id, player_id)
    if entry is None:
        entry = _make_player_entry(player_id, getattr(player, "Name", ""), owner=player_id == owner_id)
        room["players"].append(entry)
    _room_players.setdefault(room_id, {})[player_id] = player

    owner = _owner_entry(room)
    if owner is None:
        database.clear_team_membership()
        return None
    owner_id = _as_int(owner.get("plrID"))
    room_high = _room_high_ids.get(room_id, room_high)
    player.TeamID = [room_high, room_id]
    player.TeamType = _as_int(room.get("roomType"))
    player.TeamOwnerID = owner_id
    player.TeamIsOwner = player_id == owner_id
    # The client's selection is authoritative. When the client does not send
    # one, the default is 122 (Gemgrab19 / CoinRush, enabled, consistent tilemap).
    # The old default (1 = Wanted3) is disabled and does not match its tilemap.
    player.TeamMapID = _as_int(room.get("mapID", 122))
    player.SelectedMap = player.TeamMapID
    _persist_room(room)
    return room


def create_room(owner_player, room_id=None, room_type=0, room_high=0, map_id=None):
    current_team_id = getattr(owner_player, "TeamID", [0, 0])
    if current_team_id and len(current_team_id) > 1:
        current_room_id = _as_int(current_team_id[1])
        if current_room_id:
            current_room = _find_room(current_room_id) or restore_player_team(owner_player)
            if current_room is not None:
                return current_room_id

    database = _database_for_player(owner_player)
    requested_id = _as_int(room_id) if room_id is not None else 0
    if (
        requested_id <= 0
        or _find_room(requested_id) is not None
        or database.get_team_members(requested_id)
    ):
        requested_id = database.allocate_team_id()

    room_high = _as_int(room_high)
    if map_id is None:
        # The old default was index 1 (Wanted3), which is flagged Disabled and
        # has a tilemap that does not match its own mode. Index 4 (Wanted6) is
        # enabled and consistent.
        from Classes.BattleServer import _resolve_battle_location, battle_player_slots
        default_index, default_location = _resolve_battle_location(4)
        map_id = default_index

    room = {
        "id": requested_id,
        "mapID": _as_int(map_id),
        "roomType": _as_int(room_type),
        "Tick": 1,
        "premade": [],
        "msg": [],
        "invites": [],
        "players": [_make_player_entry(
            getattr(owner_player, "LowID", 0),
            getattr(owner_player, "Name", ""),
            owner=True,
            status=2,
        )],
    }
    Teams.append(room)
    _room_players[requested_id] = {
        _as_int(getattr(owner_player, "LowID", 0)): owner_player
    }
    _room_high_ids[requested_id] = room_high
    owner_player.isReady = False
    _set_player_membership(owner_player, room, _as_int(getattr(owner_player, "LowID", 0)))
    return requested_id


def add_player_to_room(room_id, player):
    room_id = _as_int(room_id)
    room = _find_room(room_id)
    if room is None:
        room = _restore_room_from_database(
            room_id,
            _database_for_player(player),
        )
    if room is None:
        return None

    player_id = _as_int(getattr(player, "LowID", 0))
    existing = get_member_record(room_id, player_id)
    if existing is not None:
        _room_players.setdefault(room_id, {})[player_id] = player
        _sync_member_record(room_id, existing)
        room_high = _room_high_ids.get(room_id, 0)
        player.TeamID = [room_high, room_id]
        owner = _owner_entry(room)
        owner_id = _as_int(owner.get("plrID")) if owner else player_id
        _set_player_membership(player, room, owner_id)
        return room

    if len(room.get("players", [])) >= 3:
        return None

    current_team_id = getattr(player, "TeamID", [0, 0])
    if current_team_id and len(current_team_id) > 1:
        current_room_id = _as_int(current_team_id[1])
        if current_room_id and current_room_id != room_id:
            remove_player_from_room(current_room_id, player)

    player.isReady = False
    room.setdefault("players", []).append(_make_player_entry(
        player_id,
        getattr(player, "Name", ""),
        owner=False,
        status=2,
    ))
    _room_players.setdefault(room_id, {})[player_id] = player
    room_high = _room_high_ids.get(room_id, 0)
    player.TeamID = [room_high, room_id]
    owner = _owner_entry(room)
    owner_id = _as_int(owner.get("plrID")) if owner else player_id
    _persist_room(room)
    return room


def remove_player_from_room(room_id, player):
    room = _find_room(room_id)
    if room is None:
        _database_for_player(player).clear_team_membership()
        player.TeamID = [0, 0]
        player.TeamType = 0
        player.TeamOwnerID = 0
        player.TeamIsOwner = False
        player.TeamMapID = 1
        return None

    room_id = _as_int(room_id)
    player_id = _as_int(getattr(player, "LowID", 0))
    leaving_was_owner = any(
        _as_int(entry.get("plrID")) == player_id and bool(entry.get("OWNER"))
        for entry in room.get("players", [])
    )
    room["players"] = [
        entry for entry in room.get("players", [])
        if _as_int(entry.get("plrID")) != player_id
    ]
    _room_players.get(room_id, {}).pop(player_id, None)

    _database_for_player(player).clear_team_membership()
    player.TeamID = [0, 0]
    player.TeamType = 0
    player.TeamOwnerID = 0
    player.TeamIsOwner = False
    player.TeamMapID = 1
    player.isReady = False

    if not room["players"]:
        Teams.remove(room)
        _room_players.pop(room_id, None)
        _room_high_ids.pop(room_id, None)
        return None

    owner = next((entry for entry in room["players"] if bool(entry.get("OWNER"))), None)
    if owner is None or leaving_was_owner:
        for entry in room["players"]:
            entry["OWNER"] = False
        room["players"][0]["OWNER"] = True
        owner = room["players"][0]
        new_owner = get_room_player(room_id, owner.get("plrID"))
        if new_owner is not None:
            # Old default was index 1 (Wanted3, disabled). Index 4 (Wanted6)
            # avoids the location glitch.
            room["mapID"] = _as_int(getattr(new_owner, "SelectedMap", room.get("mapID", 4)))
        _room_high_ids[room_id] = _as_int(getattr(new_owner, "TeamID", [0, 0])[0]) if new_owner else 0

    _persist_room(room)
    return room


def set_room_map(room_id, map_id):
    room = _find_room(room_id)
    if room is None:
        return None
    room["mapID"] = _as_int(map_id)
    _persist_room(room)
    return room


def get_disabled_bots(room_id):
    """Bot slots the owner switched off.

    Kept as a read-only stub. The 14373 client command that used to fill this
    list has been removed, so it is always empty, but TeamMessage still has to
    emit the field: the client reads its length, and without it it takes the
    terminator byte as that length and then walks past the end of the packet.
    """
    return []


# Compatibility names used by the join command.
def add_member(room_id, player):
    return add_player_to_room(room_id, player)


def get_team(room_id):
    return get_room(room_id)