from Classes.Messaging import Messaging
from Classes.Packets.PiranhaMessage import PiranhaMessage
from datetime import datetime

# The client renders the team stream by entry id and drops anything it has
# already seen, so the whole tail is resent and capped rather than picking an
# arbitrary "first two plus last" slice that is not a v29 stream delta.
MAX_ENTRIES = 50

_chat_db = None
_loaded = set()
# Entry ids are a monotonic counter, the way TeamEntry.AddStreamEntry does
# entry.Id = ++EntryCounter. Deriving the id from len(entries) instead reused
# ids after a reset and skipped them while the window was trimmed.
_counters = {}


def _database():
    """Lazily built so importing this module never touches the disk."""
    global _chat_db
    if _chat_db is None:
        from Classes.DB.ChatDB import ChatDB
        _chat_db = ChatDB()
    return _chat_db


def _persist(room_id, entry):
    """Write one chat entry to disk.

    Room ids come from DynamicDB.allocate_team_id, which is monotonic and never
    reuses a value, so a stored row always belongs to the same team. A storage
    failure must never stop the message from being delivered.
    """
    try:
        _database().addMessage(
            int(room_id or 0),
            int(entry.get("AccountIdLow", 0) or 0),
            str(entry.get("Name", "") or ""),
            1,
            int(entry.get("Type", 2) or 0),
            int(entry.get("IdLow", 0) or 0),
            str(entry.get("Message", "") or ""),
        )
        _database().prune(room_id, MAX_ENTRIES)
    except Exception:
        print(f"[TeamStream] could not persist message for room {room_id}")


def _load(room_id):
    """Read a room's history from disk the first time it is touched."""
    room_id = int(room_id or 0)
    if room_id in _loaded:
        return TeamStream2._rooms.get(room_id, [])
    _loaded.add(room_id)

    # A chat line can arrive before anything has read this room back from
    # disk. Replacing the list outright would drop it, so the two are merged
    # on id with the in-memory copy winning any conflict.
    existing = list(TeamStream2._rooms.get(room_id) or [])

    try:
        rows = _database().getRecentEntries(room_id, MAX_ENTRIES)
    except Exception:
        print(f"[TeamStream] could not load history for room {room_id}")
        TeamStream2._rooms.setdefault(room_id, existing)
        return TeamStream2._rooms[room_id]

    entries = [
        {
            "Type": int(row.get("event_type", 2) or 0),
            "IdHigh": 0,
            "IdLow": int(row.get("tick", 0) or 0),
            "AccountIdHigh": 0,
            "AccountIdLow": int(row.get("player_id", 0) or 0),
            "Name": str(row.get("player_name", "") or ""),
            "Message": str(row.get("message", "") or ""),
        }
        for row in rows
    ]

    by_id = {item["IdLow"]: item for item in entries}
    for item in existing:
        by_id[item["IdLow"]] = item

    merged = sorted(by_id.values(), key=lambda item: item["IdLow"])
    TeamStream2._rooms[room_id] = merged[-MAX_ENTRIES:]
    if merged:
        _counters[room_id] = max(item["IdLow"] for item in merged)
    return TeamStream2._rooms[room_id]


def _next_entry_id(room_id):
    value = _counters.get(room_id, 0) + 1
    _counters[room_id] = value
    return value


def _append_entry(room_id, entry):
    entries = TeamStream2._rooms.setdefault(room_id, [])
    if len(entries) >= MAX_ENTRIES:
        entries.pop(0)
    entries.append(entry)
    return entry


def add_room_chat_entry(room_id, player, message):
    """Append one chat entry to a room's stream, exactly once.

    The reference builds the entry in TeamChatReceived, assigns its id in
    TeamEntry.AddStreamEntry and then sends that one message object to every
    member. Adding the entry from inside encode would instead run once per
    recipient and repeat the line once per teammate.
    """
    entry = {
        "Type": 2,  # ChatStreamEntry
        "IdHigh": 0,
        "IdLow": _next_entry_id(room_id),
        "AccountIdHigh": 0,
        "AccountIdLow": int(getattr(player, "LowID", 0) or 0),
        "Name": str(getattr(player, "Name", "") or ""),
        "Message": message,
        "Timestamp": datetime.now().isoformat(),
    }
    _append_entry(room_id, entry)
    _persist(room_id, entry)
    return entry


def add_room_system_entry(room_id, message):
    entry = {
        "Type": 2,  # ChatStreamEntry
        "IdHigh": 0,
        "IdLow": _next_entry_id(room_id),
        "AccountIdHigh": 0,
        "AccountIdLow": 0,
        "Name": "System",
        "Message": message,
        "Timestamp": datetime.now().isoformat(),
    }
    _append_entry(room_id, entry)
    _persist(room_id, entry)
    return entry


def reset_room_entries(room_id):
    """Drop a room's chat history and restart its id counter."""
    room_id = int(room_id or 0)
    TeamStream2._rooms[room_id] = []
    _counters[room_id] = 0
    _loaded.discard(room_id)
    print(f"[TeamStream] Room {room_id} has been reset (chat history cleared)")
    return True


def room_id_for(player):
    """The real team id.

    RoomLowID was hardcoded to 1 on Player and never reassigned, so every team
    on the server shared one bucket and the TeamId on the wire never matched the
    one the client holds, which made it discard the packet.
    """
    if player is None:
        return 0
    team_id = getattr(player, "TeamID", None)
    if isinstance(team_id, (list, tuple)) and len(team_id) >= 2:
        try:
            return int(team_id[1] or 0)
        except (TypeError, ValueError):
            return 0
    try:
        return int(getattr(player, "TeamID", 0) or 0)
    except (TypeError, ValueError):
        return 0

class TeamStream2(PiranhaMessage):
    # VARIABILE DI CLASSE - Condivisa tra tutte le istanze
    _rooms = {}  # {room_id: [entries]}
    
    def __init__(self, messageData):
        super().__init__(messageData)
        self.id = 24131
        self.messageVersion = 0

    def _get_room_entries(self, room_id):
        """Entries for a room, reading them back from disk on first use."""
        if room_id not in TeamStream2._rooms:
            _load(room_id)
        return TeamStream2._rooms.setdefault(room_id, [])
    
    def _save_room_entries(self, room_id, entries):
        """Salva le entries di una room nella variabile di classe"""
        TeamStream2._rooms[room_id] = entries
    
    def add_chat_entry(self, room_id, player, message):
        """Appends one chat entry. Kept for existing callers."""
        return add_room_chat_entry(room_id, player, message)

    def add_system_entry(self, room_id, message):
        """Appends one system entry. Kept for existing callers."""
        return add_room_system_entry(room_id, message)

    @classmethod
    def reset_room(cls, room_id):
        """Resetta completamente la lista della room (usato da TeamLeave)"""
        return reset_room_entries(room_id)

    @classmethod
    def delete_room(cls, room_id):
        """Elimina completamente la room dalla memoria (usato da TeamLeave)"""
        room_id = int(room_id or 0)
        removed = cls._rooms.pop(room_id, None) is not None
        _loaded.discard(room_id)
        _counters.pop(room_id, None)
        # The team is gone, so its stored history has no reader left.
        try:
            _database().deleteMessagesByClub(room_id)
        except Exception:
            pass
        if removed:
            print(f"[TeamStream] Room {room_id} has been deleted (team disbanded)")
        return removed

    def encode(self, fields, player=None):
        """Codifica il messaggio: primi 2 + nuovi messaggi"""
        
        room_id = room_id_for(player)
        
        # Ottieni le entries della room dalla variabile di classe
        entries = self._get_room_entries(room_id)
        
        # Gestisci il messaggio
        # The entry is appended by the caller, once, before the stream is
        # broadcast. Adding it here would repeat the line once per recipient,
        # because encode runs separately for every socket this reaches.
        if fields and fields.get("AddEntry") and player:
            message = fields["Message"]

            # Controlla se è il comando .reset (chat reset, non room reset)
            if message.strip() == ".reset":
                self.reset_room(room_id)
                entries = self._get_room_entries(room_id)
                # Aggiungi messaggio di sistema dopo il reset
                self.add_system_entry(room_id, "📋 Chat history has been reset!")
                entries = self._get_room_entries(room_id)
            else:
                # Aggiungi il nuovo messaggio
                self.add_chat_entry(room_id, player, message)
                entries = self._get_room_entries(room_id)
        
        # Salva le entries locali per il debug
        self.entries = entries
        
        # === DETERMINA QUALI MESSAGGI INVIARE ===
        total_entries = len(entries)
        
        if total_entries == 0:
            # Nessun messaggio
            self.writeVInt(0)  # TeamId High
            self.writeVInt(room_id)  # TeamId Low
            self.writeVInt(0)  # Entries Length = 0
            return
        
        # Send the newest window of entries. Entry ids stay stable, so the
        # client dedups and only renders what it has not seen yet.
        messages_to_send = entries[-MAX_ENTRIES:]

        # Team ID (LogicLong) -> WriteVLong in v29, which is two VInts
        self.writeVInt(0)  # TeamId High
        self.writeVInt(room_id)  # TeamId Low
        
        # Entries Length
        self.writeVInt(len(messages_to_send))
        
        # Each Entry
        for entry in messages_to_send:
            # Base TeamStreamEntry.Encode()
            self.writeVInt(entry["Type"])  # GetStreamEntryType()
            self.writeVInt(entry["IdHigh"])  # Id High
            self.writeVInt(entry["IdLow"])   # Id Low
            self.writeVInt(entry["AccountIdHigh"])  # AccountId High
            self.writeVInt(entry["AccountIdLow"])   # AccountId Low
            self.writeString(entry["Name"])  # Name
            self.writeVInt(0)  # Campo 1
            self.writeVInt(0)  # Campo 2
            self.writeVInt(0)  # Campo 3
            
            # Campi specifici del tipo di entry
            if entry["Type"] == 2:  # ChatStreamEntry
                self.writeString(entry["Message"])
            elif entry["Type"] == 1:  # BattleStreamEntry
                self.writeVInt(entry.get("Result", 0))
                self.writeVInt(entry.get("Trophies", 0))
        
        # Debug
        entry_ids = [str(e["IdLow"]) for e in messages_to_send]
        print(f"[TeamStream] Room {room_id}: Sending {len(messages_to_send)} messages (IDs: {', '.join(entry_ids)})")
        print(f"[TeamStream] Room {room_id}: Total entries in RAM: {len(entries)}")

    def getMessageType(self):
        return 24131

    def execute(self, calling_instance, fields, cryptoInit):
        Messaging.sendMessage(24131, fields, cryptoInit, calling_instance.player)

    def getMessageVersion(self):
        return self.messageVersion
    
    @classmethod
    def clear_all_rooms(cls):
        """Pulisce tutte le room (utile per debug)"""
        cls._rooms = {}
    
    @classmethod
    def get_all_rooms(cls):
        """Ottiene tutte le room (utile per debug)"""
        return cls._rooms
    
    @classmethod
    def get_room_messages(cls, room_id):
        """Entries for a room, read back from disk on first access."""
        if int(room_id or 0) not in cls._rooms:
            _load(room_id)
        return list(cls._rooms.get(int(room_id or 0), []))
    
    @classmethod
    def get_room_count(cls):
        """Ottiene il numero di room attive"""
        return len(cls._rooms)

