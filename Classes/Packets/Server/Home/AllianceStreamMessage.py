from Classes.Logic import AllianceChat
from Classes.Packets.PiranhaMessage import PiranhaMessage


class AllianceStreamMessage(PiranhaMessage):
    """24311, the whole club chat stream.

    The previous version in Classes/two.py built the payload and then handed it
    to writeBytes, which prepends a four byte Int32 length. The client reads the
    first field as a VInt entry count, so it consumed the top three bytes of
    that prefix as the count and then read a different number of entries than
    were written.
    """

    def __init__(self, messageData):
        super().__init__(messageData)
        self.messageVersion = 0

    def encode(self, fields, player=None):
        club_low_id = int(fields.get("ClubLowID", 0) or 0)
        stream_entries = fields.get("Entries")

        # v29 writes -1 when there is no stream at all.
        if stream_entries is None and not club_low_id:
            self.writeVInt(-1)
            return

        if stream_entries is None:
            stream_entries = AllianceChat.entries(club_low_id)

        self.writeVInt(len(stream_entries))
        for entry in stream_entries:
            AllianceChat.encode_entry(self, entry)

    def decode(self):
        return {}

    def execute(self, *args, **kwargs):
        pass

    def getMessageType(self):
        return 24311

    def getMessageVersion(self):
        return self.messageVersion