"""Shared console I/O for server commands.

Provides a single stdin reader and a queue-based confirmation mechanism
so that Y/N prompts during claim overrides don't conflict with the normal
console command handler.
"""
import queue
import threading

# Shared input queue: the single stdin reader puts every line here.
STDIN_QUEUE = queue.Queue()

# When True, the console command handler ignores input (used during Y/N prompts).
CONSOLE_PAUSED = threading.Event()


def console_confirm(timeout_s=10):
    """Wait for Y/N on stdin.

    Returns True on empty Enter or Y-like, False on N-like or timeout.
    Non-case-sensitive. Pauses the normal console command handler.
    """
    CONSOLE_PAUSED.set()
    # Drain stale input
    while not STDIN_QUEUE.empty():
        try:
            STDIN_QUEUE.get_nowait()
        except Exception:
            break

    result = {"answer": None}

    def _read():
        try:
            result["answer"] = STDIN_QUEUE.get(timeout=timeout_s)
        except Exception:
            result["answer"] = None

    reader = threading.Thread(target=_read, daemon=True)
    reader.start()
    reader.join(timeout_s + 0.5)

    CONSOLE_PAUSED.clear()

    if result["answer"] is None:
        print(f"[517] nessun comando ricevuto entro {timeout_s}s -> OutOfSync")
        return False
    answer = result["answer"].strip().upper()
    if answer == "" or answer in ("Y", "YES", "S", "SI", "SÌ"):
        return True
    if answer in ("N", "NO"):
        return False
    print(f"[517] risposta '{answer}' non riconosciuta -> OutOfSync")
    return False


def is_paused():
    return CONSOLE_PAUSED.is_set()
