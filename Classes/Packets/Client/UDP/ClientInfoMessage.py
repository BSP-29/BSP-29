from Classes.Packets.PiranhaMessage import PiranhaMessage
from Classes.Messaging import Messaging


class ClientInfoMessage(PiranhaMessage):
    """Client request for the UDP endpoint used by its current battle."""

    def __init__(self, messageData):
        super().__init__(messageData)
        self.messageVersion = 0

    def encode(self, fields):
        pass

    def decode(self):
        return {}

    def execute(self, calling_instance, fields, cryptoInit):
        session_id = int(getattr(calling_instance, "udp_session_id", 0) or 0)
        # This request is the only thing that makes a client open its UDP
        # socket, so say plainly when one arrives. Its absence is the signal
        # that the client is stuck before the point where it would ask.
        print(f"[UDP] 10177 ClientInfo received, session {session_id}. The "
              f"client has reached the point where it wants to talk over UDP.")

        import Configuration
        from Classes.BattleServer import get_udp_server_address, udp_info_fields

        advertised_address = get_udp_server_address(getattr(calling_instance, "address", None))
        if not advertised_address:
            print("[UDP] ClientInfo received but no UDP server address could be resolved")
            return
        Messaging.sendMessage(
            24112,
            udp_info_fields(calling_instance, None, session_id),
            cryptoInit,
            calling_instance.player,
        )

    def getMessageType(self):
        return 10177

    def getMessageVersion(self):
        return self.messageVersion
