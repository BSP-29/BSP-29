# 14372 arrives from the client as part of the team lobby settings UI.
#
# The v29 reference has no 14372 and no GadgetStatus anywhere, so there is no
# server side behaviour for it. The previous implementation toggled a flag,
# answered with OutOfSync and then closed the socket 0.8s later, which tore
# the connection down from inside a routine lobby toggle. Unknown messages are
# simply absorbed here.
from Classes.Packets.PiranhaMessage import PiranhaMessage


class TeamToggleSettingsMessage(PiranhaMessage):
    def __init__(self, messageData):
        super().__init__(messageData)
        self.messageVersion = 0

    def decode(self):
        fields = {}
        super().decode(fields)
        return fields

    def encode(self, fields, player=None):
        pass

    def execute(self, calling_instance, fields, cryptoInit):
        # Nothing to do. Answering with OutOfSync or dropping the socket here
        # made the lobby look like it randomly changed state.
        return

    def getMessageType(self):
        # Matches the key this class is registered under in the factory. It
        # previously returned 14777, which is SetInvitesBlockedMessage.
        return 14372

    def getMessageVersion(self):
        return self.messageVersion