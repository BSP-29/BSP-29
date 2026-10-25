from threading import Lock, Timer, Timer

from Classes.ClientsManager import ClientsManager
from Classes.Messaging import Messaging
from Classes.TeamManager import get_room, get_room_player, get_room_players

# The v29 reference manages matchmaking through MatchmakingSlot objects that
# are updated on a timer. SEARCH_TIMEOUT is 0, which means the slot starts the
# game on its first update tick with whatever is in the queue and empties it,
# so 20405 is never actually sent in that path. The previous version sent it
# unconditionally with an arbitrary countdown, which is the transition we now
# suspect when the client freezes between the two screens.

_matchmaking_lock = Lock()

SEARCH_TIMEOUT = 0

# Each room that starts matchmaking gets its own small state, the way the
# reference manages MatchmakingEntry objects per slot.
class _MatchmakingState:
    def __init__(self, room):
        self.room = room
        self.queue = list(room.get("players", []))
        self.turns = 0
        self.seconds_left = SEARCH_TIMEOUT
        self.started = False


# Per-room state, keyed by the same room_id the rest of the module uses.
_matchmaking_states = {}

# A lightweight timer that drives the matchmaking loop continuously, the way
# Royale's Update() loop runs on its own clock. Without it the state sits
# unprocessed and nothing ever starts.
_matchmaking_timer = None


def _matchmaking_timer_tick():
    try:
        for room_id in list(_matchmaking_states.keys()):
            _tick_matchmaking(room_id)
        # The reference loop sleeps; here we reschedule immediately for the
        # same responsiveness without blocking.
        global _matchmaking_timer
        _matchmaking_timer = Timer(0.05, _matchmaking_timer_tick)
        _matchmaking_timer.start()
    except Exception as error:
        print(f"[TeamMatchmaking] tick error: {error}")


def send_matchmaking_status():
    """Whether 20405 is sent when a match starts.

    The v29 reference never reaches the line that sends it in normal
    matchmaking because SEARCH_TIMEOUT = 0 empties the queue on the first tick.
    Leave false to match that behaviour.
    """
    import Configuration
    return bool(Configuration.settings.get("SendMatchmakingStatus", False))


def skip_battle_start():
    """Whether to stop after the matchmaking status and not start the battle.

    For bisecting the freeze. With this on the client receives 20405 and no
    battle packets at all, so a screen that still stalls is not caused by 24130,
    20559 or anything that follows them.
    """
    import Configuration
    return bool(Configuration.settings.get("SkipBattleStart", False))


def _online_session(player):
    session = getattr(player, "session", None)
    if session is None or not hasattr(session, "client") or not hasattr(session, "cryptoInit"):
        return None

    player_id = int(getattr(player, "LowID", 0) or 0)
    client_data = ClientsManager.GetAll().get(player_id)
    if not client_data or client_data.get("Session") is not session:
        return None
    return session


def _send_to_room(room_id, message_type, fields=None):
    for member in get_room_players(room_id):
        session = _online_session(member)
        if session is None:
            continue
        payload = {"Socket": session.client}
        if fields:
            payload.update(fields)
        Messaging.sendMessage(
            message_type,
            payload,
            session.cryptoInit,
            member,
        )


def member_is_in_battle(member):
    """Whether this member already owns a live battle session.

    24124 is a team lobby snapshot. Once a member has been sent 20559 the client
    is on the loading screen, and a lobby snapshot arriving on top of it pulls it
    back out to the lobby, which is what stalled the match start.
    """
    session = getattr(member, "session", None)
    if session is not None:
        if int(getattr(session, "udp_session_id", 0) or 0) > 0:
            return True
        try:
            from Classes.BattleServer import is_session_in_battle
            if is_session_in_battle(session):
                return True
        except Exception:
            pass
    return int(getattr(member, "battle_session_id", 0) or 0) > 0


def broadcast_team(room_id):
    """Send 24124 to every member that is still in the lobby.

    Members that already have a battle session are skipped. The reference
    broadcasts to whoever is online, but by the time a member has been given a
    20559 their team state is frozen and the lobby snapshot is stale.
    """
    for member in get_room_players(room_id):
        if member_is_in_battle(member):
            continue
        session = _online_session(member)
        if session is None:
            continue
        Messaging.sendMessage(
            24124,
            {"Socket": session.client},
            session.cryptoInit,
            member,
        )


def all_members_ready(room_id):
    room = get_room(room_id)
    if room is None:
        return False

    entries = room.get("players", [])
    if not entries:
        return False

    for entry in entries:
        player_id = int(entry.get("plrID", 0) or 0)
        member = get_room_player(room_id, player_id)
        if member is None or _online_session(member) is None:
            return False
        if not bool(entry.get("READY", False)) or not bool(getattr(member, "isReady", False)):
            return False
    return True


def _tick_matchmaking(room_id):
    state = _matchmaking_states.get(room_id)
    if state is None:
        return
    # SEARCH_TIMEOUT = 0 means the reference's slot starts the game with whatever
    # members it has on the first tick and empties the queue. 20405 is never sent.
    # The tick loop keeps the state alive for vision frame distribution after the
    # game has started.
    if state.queue and not state.started:
        state.turns += 1
        if state.turns >= 4:
            state.turns = 0
            state.seconds_left -= 1
        # With SEARCH_TIMEOUT = 0, any members present mean the game starts now.
        if state.seconds_left <= 0 or state.queue:
            state.seconds_left = SEARCH_TIMEOUT
            from Classes.BattleServer import start_team_battle
            from Classes.TeamMatchmaking import skip_battle_start
            if not skip_battle_start():
                state.started = True
                start_team_battle(room_id)
            # After the game starts the matchmaking state is cleaned up by the
            # tick loop; here we just mark it started.
        return
    else:
        state.turns = 0
        state.seconds_left = SEARCH_TIMEOUT


def start_matchmaking(room_id):
    with _matchmaking_lock:
        room = get_room(room_id)
        if room is None or room.get("matchmakingStarted") or not all_members_ready(room_id):
            return False

        room["matchmakingStarted"] = True
        room["_matchmakingPreviousStats"] = {}
        for entry in room.get("players", []):
            player_id = int(entry.get("plrID", 0) or 0)
            room["_matchmakingPreviousStats"][player_id] = int(entry.get("STAT", 2) or 0)
            entry["STAT"] = 4

        broadcast_team(room_id)

        # The reference's SEARCH_TIMEOUT = 0 means the slot starts the game on
        # the first tick with whatever is in the queue. 20405 is never sent in
        # that path. We leave it off by default, but the flag lets us compare.
        if send_matchmaking_status():
            from Classes.BattleServer import battle_player_slots
            slots = battle_player_slots(room.get("mapID"))
            _send_to_room(room_id, 20405, {
                "Timer": 0,
                "PlayersFound": len(room.get("players", [])),
                "MaxPlayers": slots,
                "Searching": True,
            })

        # Initialize and start the continuous tick loop.
        state = _MatchmakingState(room)
        for entry in room.get("players", []):
            player_id = int(entry.get("plrID", 0) or 0)
            from Classes.TeamManager import get_room_player
            member = get_room_player(room_id, player_id)
            if member is not None and _online_session(member) is not None:
                state.queue.append(member)
        _matchmaking_states[room_id] = state

        if not skip_battle_start():
            # Claim the start BEFORE the timer is armed. The timer fires 50 ms
            # from now, and a start_team_battle that takes longer than that
            # would otherwise let _tick_matchmaking see a still-empty started
            # flag and begin a second battle on another thread. That only stays
            # harmless because _start_battle refuses a room id it already has
            # in _battles, which is an accident waiting to depend on.
            state.started = True

        # Start the timer loop right away so the first tick fires in 50ms.
        global _matchmaking_timer
        if _matchmaking_timer is not None:
            try:
                _matchmaking_timer.cancel()
            except Exception:
                pass
        _matchmaking_timer = Timer(0.05, _matchmaking_timer_tick)
        _matchmaking_timer.start()

        if skip_battle_start():
            # The tick loop owns the start. Without this the battle would be
            # sent here anyway and the flag would never bisect anything.
            return True

        from Classes.BattleServer import start_team_battle
        result = start_team_battle(room_id)
        if not result:
            room["matchmakingStarted"] = False
            for entry in room.get("players", []):
                player_id = int(entry.get("plrID", 0) or 0)
                entry["STAT"] = room.get("_matchmakingPreviousStats", {}).get(player_id, 2)
            room.pop("_matchmakingPreviousStats", None)
            broadcast_team(room_id)
            # Clean up even on failure.
            _matchmaking_states.pop(room_id, None)
            return False
        # Do not clean up the state: the background tick loop uses it.
    return True


def cancel_matchmaking(room_id, reset_ready=True):
    with _matchmaking_lock:
        room = get_room(room_id)
        if room is None:
            return False

        room["matchmakingStarted"] = False
        previous_stats = room.pop("_matchmakingPreviousStats", {})
        for entry in room.get("players", []):
            player_id = int(entry.get("plrID", 0) or 0)
            entry["STAT"] = previous_stats.get(player_id, 2)

        # Clean up the tick state.
        _matchmaking_states.pop(room_id, None)

        if reset_ready:
            for entry in room.get("players", []):
                entry["READY"] = False
                member = get_room_player(room_id, entry.get("plrID", 0))
                if member is not None:
                    member.isReady = False

        _send_to_room(room_id, 20406)
        if reset_ready:
            broadcast_team(room_id)
    return True
