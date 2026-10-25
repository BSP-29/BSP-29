"""Club chat stream, mirroring the v29 AllianceStream.

Entries are kept in RAM per club with a monotonically increasing id, and the
oldest is dropped once the list reaches MAX_ENTRIES. History is also written to
ChatDB so it survives a restart, and a club is read back from disk the first
time it is touched.
"""
import time

MAX_ENTRIES = 200
# How much history is read back from disk for a club.
LOAD_ENTRIES = 200

ENTRY_TYPE_CHAT = 2
ENTRY_TYPE_EVENT = 4

_streams = {}
_counters = {}
_loaded = set()
_db = None


def _database():
    """Lazily built so importing this module never touches the disk."""
    global _db
    if _db is None:
        from Classes.DB.ChatDB import ChatDB
        _db = ChatDB()
    return _db


def _counter(club_low_id):
    value = _counters.get(club_low_id, 0) + 1
    _counters[club_low_id] = value
    return value


def add_chat_message(club_low_id, author_id, author_name, author_role, content):
    entry = {
        "Type": ENTRY_TYPE_CHAT,
        "Id": _counter(club_low_id),
        "AuthorId": author_id,
        "AuthorName": author_name,
        "AuthorRole": author_role,
        "SentAt": int(time.time()),
        "Message": content,
    }
    _append(club_low_id, entry)
    _persist(club_low_id, entry)
    return entry


def add_event(club_low_id, event, player_id, player_name, author_role=1):
    entry = {
        "Type": ENTRY_TYPE_EVENT,
        "Id": _counter(club_low_id),
        "AuthorId": player_id,
        "AuthorName": player_name,
        "AuthorRole": author_role,
        "SentAt": int(time.time()),
        "Event": event,
        "PlayerId": player_id,
        "PlayerName": player_name,
    }
    _append(club_low_id, entry)
    _persist(club_low_id, entry)
    return entry


def _persist(club_low_id, entry):
    """Write one entry to disk. A storage failure must not drop the message."""
    try:
        database = _database()
        database.addMessage(
            int(club_low_id or 0),
            int(entry.get("AuthorId", 0) or 0),
            str(entry.get("AuthorName", "") or ""),
            int(entry.get("AuthorRole", 1) or 0),
            int(entry.get("Type", ENTRY_TYPE_CHAT) or 0),
            int(entry.get("Id", 0) or 0),
            str(entry.get("Message", "") or ""),
        )
        database.prune(club_low_id, MAX_ENTRIES)
    except Exception:
        print(f"[AllianceChat] could not persist message for club {club_low_id}")


def _load(club_low_id):
    """Read a club's history from disk the first time it is touched."""
    club_low_id = int(club_low_id or 0)
    if club_low_id in _loaded:
        return _streams.get(club_low_id, [])
    _loaded.add(club_low_id)

    # A message can arrive before anything has read this club back from disk.
    # Replacing the list outright would drop it, so the two are merged on id
    # with the in-memory copy winning any conflict.
    existing = list(_streams.get(club_low_id) or [])

    try:
        rows = _database().getRecentEntries(club_low_id, LOAD_ENTRIES)
    except Exception:
        print(f"[AllianceChat] could not load history for club {club_low_id}")
        _streams.setdefault(club_low_id, existing)
        return _streams[club_low_id]

    entries = []
    for row in rows:
        entry_type = int(row.get("event_type", ENTRY_TYPE_CHAT) or 0)
        entry = {
            "Type": entry_type,
            "Id": int(row.get("tick", 0) or 0),
            "AuthorId": int(row.get("player_id", 0) or 0),
            "AuthorName": str(row.get("player_name", "") or ""),
            "AuthorRole": int(row.get("player_role", 1) or 0),
            "SentAt": int(time.time()),
            "Message": str(row.get("message", "") or ""),
        }
        if entry_type == ENTRY_TYPE_EVENT:
            entry["Event"] = int(row.get("message", 0) or 0)
            entry["PlayerId"] = int(row.get("player_id", 0) or 0)
            entry["PlayerName"] = str(row.get("player_name", "") or "")
        entries.append(entry)

    by_id = {item["Id"]: item for item in entries}
    for item in existing:
        by_id[item["Id"]] = item

    merged = sorted(by_id.values(), key=lambda item: item["Id"])
    _streams[club_low_id] = merged[-MAX_ENTRIES:]
    if merged:
        _counters[club_low_id] = max(item["Id"] for item in merged)
    return _streams[club_low_id]


def _append(club_low_id, entry):
    entries = _streams.setdefault(club_low_id, [])
    if len(entries) >= MAX_ENTRIES:
        entries.pop(0)
    entries.append(entry)
    return entry


def entries(club_low_id):
    return list(_load(club_low_id))


def clear(club_low_id):
    _streams.pop(int(club_low_id or 0), None)
    _counters.pop(int(club_low_id or 0), None)
    _loaded.discard(int(club_low_id or 0))


def online_members(club_low_id):
    """Online players belonging to this club.

    Filtered from the live connection table rather than the alliance member
    table, so this cannot depend on the shape of AllianceDB.getMembers.
    """
    from Classes.ClientsManager import ClientsManager

    club_low_id = int(club_low_id or 0)
    found = []
    for player_id, data in list(ClientsManager.GetAll().items()):
        session = data.get("Session")
        member = getattr(session, "player", None)
        if member is None:
            continue
        if int(getattr(member, "ClubLowID", 0) or 0) != club_low_id:
            continue
        if not hasattr(session, "client") or not hasattr(session, "cryptoInit"):
            continue
        found.append(member)
    return found


def encode_entry(stream, entry):
    """Write one AllianceStreamEntry.

    Shared by 24311 and 24312 so the two cannot drift apart. Ids are LogicLongs,
    which means high and low written as two VInts, not as an eight byte Int pair.
    """
    stream.writeVInt(int(entry.get("Type", ENTRY_TYPE_CHAT) or 0))

    stream.writeVInt(0)
    stream.writeVInt(int(entry.get("Id", 0) or 0))

    stream.writeVInt(0)
    stream.writeVInt(int(entry.get("AuthorId", 0) or 0))

    stream.writeString(str(entry.get("AuthorName", "") or ""))
    stream.writeVInt(int(entry.get("AuthorRole", 1) or 0))
    stream.writeVInt(_elapsed_seconds(entry))
    stream.writeVInt(0)

    if int(entry.get("Type", 0) or 0) == ENTRY_TYPE_EVENT:
        stream.writeVInt(int(entry.get("Event", 0) or 0))
        stream.writeVInt(1)
        stream.writeVInt(0)
        stream.writeVInt(int(entry.get("PlayerId", 0) or 0))
        stream.writeString(str(entry.get("PlayerName", "") or ""))
    else:
        stream.writeString(str(entry.get("Message", "") or ""))


def encode_empty_entry(stream):
    """A single unset entry, matching the entry shape with every field zeroed."""
    encode_entry(stream, {
        "Type": 0,
        "Id": 0,
        "AuthorId": 0,
        "AuthorName": "",
        "AuthorRole": 0,
        "SentAt": 0,
        "Message": "",
    })


def _elapsed_seconds(entry):
    sent_at = int(entry.get("SentAt", 0) or 0)
    if not sent_at:
        return 0
    elapsed = int(time.time()) - sent_at
    return elapsed if elapsed >= 0 else 0