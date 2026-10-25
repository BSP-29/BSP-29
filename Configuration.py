# DisableNagle: reduce delay and improve performance between client and server BUT require more power #

import os

_DEFAULT_SETTINGS = {
    "DisableNagle": True,
    "PrintEnabled": True,
    "TCPHost": "0.0.0.0",
    "TCPPort": 9339,
    "UDPHost": "0.0.0.0",
    "UDPPort": 9339,
    "UDPServerAddress": "bsp67.dedyn.io",

    # Battle start. RunBattleSimulation off stops the 20 Hz character tick and
    # the vision stream, which a client playing locally as offline practice
    # never reads. SendTeamGameStarting off withholds 24130: the reference only
    # ever sends it from Teams.StartGame, which is commented out, so putting it
    # on the wire tells the client to start a game the server never requested
    # and desynchronises the two sides.
    "RunBattleSimulation": True,
    "SendTeamGameStarting": False,
    # Send 24112 (UDP endpoint) right after the 20559 loading screen, as the v29
    # reference does, instead of waiting for the client to ask with 10177.
    "SendUdpInfoWithLoading": True,
    "ResolveClientAddress": True,
    # How 24112 fills its leading fields. "sessionfirst" puts the session id
    # in the first VInt and sends the address as host:port. "reference" puts
    # the UDP port there, sends a bare IP, and makes the ten byte token the
    # session header the client echoes on every datagram.
    "UdpInfoMode": "sessionfirst",
    "ProbeClientUdp": True,
    "SpectateMode": False,
    "SendMatchmakingStatus": False,
    "SkipBattleStart": False,
    # Fallback location, used only when the client has not chosen one. The map
    # a client picks arrives in 14363 into room["mapID"] and in the last vint of
    # 14103, and that always wins. Empty means "use the built-in default", which
    # is Wanted6, an enabled BountyHunter location. Accepts an index or a name.
    "BattleLocation": "",
    "UdpDnsResolver": "1.1.1.1",
    "UdpDnsTimeout": 1500,

    # Diagnostics. DumpPackets prints every id in DumpMessageIds as hex before
    # encryption, and 24124 also gets the field list recorded by the encoder.
    "DumpPackets": False,
    "DumpMessageIds": "24124,24131,24311,24312",

    # Team slots advertised in 24124. The v29 reference sends 3, and neither it
    # nor v26 nor v28 ever puts the disabled bot slot list on the wire, so a
    # capacity above 1 makes the client draw bot slots the server cannot switch
    # off. Use 1 to keep the lobby free of them.
    "TeamCapacity": 3,
}

# Keys that must stay integers, because callers do arithmetic or byte layout on
# them rather than passing them straight to an API that accepts strings.
_INT_KEYS = ("TCPPort", "UDPPort", "UdpDnsTimeout")

# Keys that must stay booleans. Only these get textual boolean coercion, so a
# hostname or path that happens to read "true" is never mangled into a bool.
_BOOL_KEYS = (
    "DisableNagle",
    "PrintEnabled",
    "RunBattleSimulation",
    "SendTeamGameStarting",
    "SendUdpInfoWithLoading",
    "ResolveClientAddress",
    "ProbeClientUdp",
    "SpectateMode",
    "SendMatchmakingStatus",
    "SkipBattleStart",
    "SendStartLoading",
    "DumpPackets",
)

_BOOL_TRUE = ("true", "yes", "on", "1")
_BOOL_FALSE = ("false", "no", "off", "0")

_PROPERTIES_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "server.properties"
)


def _parse_properties(path):
    """Read a flat key=value file. Both '=' and ':' separate, '#' starts a comment."""
    values = {}
    try:
        with open(path, "r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line or line.startswith("#") or line.startswith("!"):
                    continue
                for separator in ("=", ":"):
                    if separator in line:
                        key, _, value = line.partition(separator)
                        key = key.strip()
                        value = value.strip()
                        if key:
                            values[key] = value
                        break
    except OSError:
        return values
    return values


def _coerce(key, value):
    if key in _INT_KEYS:
        try:
            return int(str(value).strip())
        except (TypeError, ValueError):
            return value
    if key in _BOOL_KEYS:
        text = str(value).strip().lower()
        if text in _BOOL_TRUE:
            return True
        if text in _BOOL_FALSE:
            return False
        return value
    return value


def _load():
    settings = dict(_DEFAULT_SETTINGS)

    if not os.path.isfile(_PROPERTIES_FILE):
        print(f"[Config] No {_PROPERTIES_FILE}, using built-in defaults")
        return settings

    parsed = _parse_properties(_PROPERTIES_FILE)
    if not parsed:
        print(f"[Config] {_PROPERTIES_FILE} is empty, using built-in defaults")
        return settings

    overridden = []
    added = []
    for key, raw in parsed.items():
        value = _coerce(key, raw)
        if key in settings:
            if settings[key] != value:
                overridden.append(f"{key}={settings[key]!r} -> {value!r}")
            settings[key] = value
        else:
            added.append(key)
            settings[key] = value

    print(f"[Config] Loaded {len(parsed)} entries from {os.path.basename(_PROPERTIES_FILE)}")
    for entry in overridden:
        print(f"[Config]   override {entry}")
    for key in added:
        print(f"[Config]   new key '{key}' is not read anywhere in the code")

    for key in _INT_KEYS:
        print(f"[Config]   {key} = {settings.get(key)!r}")

    return settings


settings = _load()