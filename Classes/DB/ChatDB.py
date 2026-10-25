"""SQLite storage for club and team chat history.

The previous version was truncated mid-method, had no close() even though
Player.close_databases() calls one, used a relative path that breaks when the
working directory differs, and opened a fresh connection for every Player
construction. Connections are now shared per resolved path and guarded by a
lock, because Connection is a thread and the same handle was touched from more
than one of them.
"""
import os
import sqlite3
import threading

_DEFAULT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "database",
    "chat.db",
)

_connections = {}
_lock = threading.Lock()
_write_lock = threading.RLock()


def _connection_for(path):
    """One shared connection per path."""
    with _lock:
        conn = _connections.get(path)
        if conn is None:
            conn = sqlite3.connect(path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            try:
                conn.execute("PRAGMA journal_mode=WAL")
            except sqlite3.DatabaseError:
                pass
            _connections[path] = conn
        return conn


class ChatDB:
    """Chat history store. Safe to construct more than once for the same file."""

    def __init__(self, db_path=None):
        self.db_path = db_path or _DEFAULT_PATH
        parent = os.path.dirname(os.path.abspath(self.db_path))
        if parent:
            os.makedirs(parent, exist_ok=True)
        self.conn = _connection_for(self.db_path)
        self.create_tables()

    def create_tables(self):
        with _write_lock:
            cursor = self.conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_message (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    club_id INTEGER NOT NULL,
                    player_id INTEGER NOT NULL,
                    player_name TEXT NOT NULL,
                    player_role INTEGER DEFAULT 1,
                    event_type INTEGER DEFAULT 0,
                    tick INTEGER DEFAULT 0,
                    message TEXT DEFAULT '',
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_chat_club ON chat_message (club_id, id)"
            )
            self.conn.commit()

    # ==================== WRITE ====================

    def addMessage(self, club_id, player_id, player_name, player_role,
                   event_type, tick, message=""):
        """Append one entry and return its row id."""
        with _write_lock:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO chat_message
                (club_id, player_id, player_name, player_role, event_type, tick, message)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (club_id, player_id, player_name, player_role, event_type, tick, message))
            self.conn.commit()
            return cursor.lastrowid

    # ==================== READ ====================

    def getMessages(self, club_id, limit=100):
        """Most recent entries first returned, oldest first in the list."""
        return self.getRecentEntries(club_id, limit)

    def getRecentEntries(self, club_id, limit=100):
        """Rows shaped for the chat encoders: id, type, author and message."""
        try:
            limit = int(limit)
        except (TypeError, ValueError):
            limit = 100
        if limit <= 0:
            return []
        with _write_lock:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT id, club_id, player_id, player_name, player_role,
                       event_type, tick, message
                FROM chat_message
                WHERE club_id = ?
                ORDER BY id DESC
                LIMIT ?
            """, (int(club_id or 0), limit))
            rows = [dict(row) for row in cursor.fetchall()]
        rows.reverse()
        return rows

    def getMessageCount(self, club_id):
        with _write_lock:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) AS count FROM chat_message WHERE club_id = ?",
                (int(club_id or 0),),
            )
            row = cursor.fetchone()
        return row["count"] if row else 0

    def getMessagesByPlayer(self, club_id, player_id, limit=100):
        with _write_lock:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT id, club_id, player_id, player_name, player_role,
                       event_type, tick, message
                FROM chat_message
                WHERE club_id = ? AND player_id = ?
                ORDER BY id DESC
                LIMIT ?
            """, (int(club_id or 0), int(player_id or 0), int(limit or 100)))
            rows = [dict(row) for row in cursor.fetchall()]
        rows.reverse()
        return rows

    # ==================== DELETE ====================

    def deleteMessage(self, message_id):
        with _write_lock:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM chat_message WHERE id = ?", (message_id,))
            self.conn.commit()
            return cursor.rowcount > 0

    def deleteMessagesByClub(self, club_id):
        """Drop a club's history, used when the club itself is removed."""
        with _write_lock:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM chat_message WHERE club_id = ?", (int(club_id or 0),))
            self.conn.commit()
            return cursor.rowcount > 0

    def prune(self, club_id, keep=200):
        """Keep only the newest `keep` rows for a club, then return how many went."""
        with _write_lock:
            cursor = self.conn.cursor()
            cursor.execute("""
                DELETE FROM chat_message
                WHERE club_id = ? AND id NOT IN (
                    SELECT id FROM chat_message
                    WHERE club_id = ? ORDER BY id DESC LIMIT ?
                )
            """, (int(club_id or 0), int(club_id or 0), int(keep)))
            self.conn.commit()
            return cursor.rowcount

    def close(self):
        """Kept for Player.close_databases(), which used to raise AttributeError.

        The handle is shared, so it is intentionally left open for reuse.
        """
        return None