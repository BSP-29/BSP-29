"""Packet dumps for diagnosing stream alignment.

The client runs in an emulator here, so it cannot be captured directly. Dumping
what the server produces is the next best thing.

The field list is recorded by the encoder itself, through
Classes.ByteStream._WriteTrace, rather than by re-parsing the finished payload.
Re-parsing would mean keeping a second implementation of the layout, and the
one written here already disagreed with the real encoder once. Recording the
original writes cannot disagree with them by construction.

Dumps happen before encryption, so what is printed is the plaintext payload.
"""
import Configuration

_watched = None


def watched_types():
    global _watched
    if _watched is None:
        raw = str(Configuration.settings.get("DumpMessageIds", "") or "")
        wanted = set()
        for part in raw.replace(";", ",").split(","):
            part = part.strip()
            if part.isdigit():
                wanted.add(int(part))
        _watched = wanted
    return _watched


def reset():
    global _watched
    _watched = None


def should_dump(message_type):
    if not Configuration.settings.get("DumpPackets", False):
        return False
    return int(message_type) in watched_types()


def dump(message_type, payload, note=""):
    payload = bytes(payload or b"")
    print(f"\n[DUMP] message {message_type} len={len(payload)}{(' ' + note) if note else ''}")
    for start in range(0, len(payload), 16):
        chunk = payload[start:start + 16]
        print(f"[DUMP] {start:04x}  {chunk.hex(' ')}")


def render_trace(trace, message_type, payload):
    """Print the recorded write list next to the hex."""
    payload = bytes(payload or b"")
    dump(message_type, payload)
    print(f"[DUMP] --- field list, recorded by the encoder ({message_type}) ---")
    for line in trace.render():
        print(line)
    consumed = trace.entries[-1][0] if trace.entries else 0
    print(f"[DUMP] --- {len(trace.entries)} fields recorded, "
          f"payload is {len(payload)} bytes ---")