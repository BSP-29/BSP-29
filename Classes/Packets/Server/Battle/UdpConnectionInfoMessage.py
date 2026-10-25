import struct

from Classes.Packets.PiranhaMessage import PiranhaMessage


class UdpConnectionInfoMessage(PiranhaMessage):
    """Tells the client the UDP server IP, port and tokens to open a socket.

    Default layout:

        vint    BattleID, the session id
        string  ServerIP, which carries the port, so "1.2.3.4:9339"
        int     token length, then that many bytes
        int     key length, then that many bytes

    UdpInfoMode=reference keeps the v29 reference encoding instead, where the
    first field is the UDP port and the ten byte token is the session header
    the client echoes at the head of every datagram, which is how
    _handle_datagram matches a packet to its session.
    """

    def __init__(self, messageData):
        super().__init__(messageData)
        self.messageVersion = 0

    def encode(self, fields, player=None):
        # 1. BattleID / SessionID (VInt), or the UDP port in reference mode
        if fields.get("SessionFirst"):
            self.writeVInt(int(fields.get("BattleID", fields.get("SessionID", 0)) or 0))
        else:
            self.writeVInt(int(fields.get("Port", 9339) or 9339))

        # 2. IP del server UDP (String) - puo' includere la porta, es. "1.2.3.4:9339"
        if fields.get("SessionFirst"):
            self.writeString(str(fields.get("ServerIP", "") or ""))
        else:
            self.writeString(str(fields.get("Address", "") or ""))

        # 3. Token (Array di byte: writeInt(len) + bytes)
        token = bytes(fields.get("Token", b"") or b"")
        self.writeInt(len(token))
        if token:
            self.messagePayload += token
            self.offset += len(token)

        # 4. Chiave (Array di byte: writeInt(len) + bytes)
        key = bytes(fields.get("Key", b"") or b"")
        self.writeInt(len(key))
        if key:
            self.messagePayload += key
            self.offset += len(key)

    def decode(self):
        return {}

    def execute(self, *args, **kwargs):
        pass

    def getMessageType(self):
        return 24112

    def getMessageVersion(self):
        return self.messageVersion
