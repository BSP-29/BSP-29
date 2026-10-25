import traceback
from Classes.Logic.LogicLaserMessageFactory import LogicLaserMessageFactory
from Classes.Messaging import Messaging


class MessageManager:
    def receiveMessage(self, messageType, messagePayload, cryptoInit):
        message = LogicLaserMessageFactory.createMessageByType(messageType, messagePayload)
        if message is not None:
            try:
                if message.isServerToClient():
                    message.encode()
                else:
                    message.fields = message.decode()
                    # Passa cryptoInit (che è la connessione) e il suo crypto
                    message.execute(self, message.fields, cryptoInit)

            except Exception:
                print(traceback.format_exc())
        # Preserve the legacy home refresh only while the connection is in the
        # lobby; the v29 battle flow ignores unrelated TCP messages here.
        player = getattr(self, "player", None)
        # The v29 reference keeps the UDP session on the TCP Connection. The
        # player's in-memory model can be a separate room/member object, so it
        # is not a reliable signal during the StartLoading transition. The
        # battle session registry is the authoritative one.
        in_battle = (
            int(getattr(self, "udp_session_id", 0) or 0) > 0
            or int(getattr(player, "battle_session_id", 0) or 0) > 0
        )
        if not in_battle:
            try:
                from Classes.BattleServer import is_session_in_battle
                in_battle = is_session_in_battle(self)
            except Exception:
                pass

        if messageType > 10100 and messageType not in (10177, 14103, 14355) and not in_battle:
            # 23457 is the v29 LobbyInfoMessage, which tells the client to show
            # the lobby. Logged because sending it during a match start is what
            # pulls the client back out of the battle.
            print(f"[MSG] {messageType} not in battle -> sending 23457 lobby refresh")
            Messaging.sendMessage(23457, {"Socket": self.client}, cryptoInit, self.player)
