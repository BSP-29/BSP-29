from Classes.Logic import AllianceChat
from Classes.Messaging import Messaging
from Classes.Packets.PiranhaMessage import PiranhaMessage


class AskForAllianceStreamMessage(PiranhaMessage):
    """14304, the client asking for club chat history.

    It was a bare string placeholder, so the club chat history could never be
    requested at all. The v29 reference only implements the server side of this
    exchange, so the request payload is read defensively: whatever VInts are
    present are taken as club id then last seen entry id.
    """

    def __init__(self, messageData):
        super().__init__(messageData)
        self.messageVersion = 0
        self.clubLowID = 0
        self.lastSeenIndex = -1

    def encode(self, fields, player=None):
        pass

    def decode(self):
        fields = {}

        if self.offset < self.length:
            self.clubLowID = self.readVInt()
        if self.offset < self.length:
            value = self.readVInt()
            # A negative cursor is how the protocol spells "send me everything".
            self.lastSeenIndex = -1 if value < 0 else value

        super().decode(fields)
        return fields

    def execute(message, calling_instance, fields, cryptoInit):
        player = calling_instance.player
        # The club is taken from the session, not from the request, so a client
        # cannot ask for another club's stream.
        club_low_id = int(getattr(player, "ClubLowID", 0) or 0)
        if not club_low_id:
            return

        stream_entries = AllianceChat.entries(club_low_id)
        cursor = message.lastSeenIndex
        if cursor >= 0:
            stream_entries = stream_entries[cursor:]

        fields["Socket"] = calling_instance.client
        fields["ClubLowID"] = club_low_id
        fields["Entries"] = stream_entries
        Messaging.sendMessage(24311, fields, cryptoInit, player)

    def getMessageType(self):
        return 14304

    def getMessageVersion(self):
        return self.messageVersion