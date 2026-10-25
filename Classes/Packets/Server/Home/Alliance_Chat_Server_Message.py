from Classes.Logic import AllianceChat
from Classes.Packets.PiranhaMessage import PiranhaMessage


class AllianceChatServerMessage(PiranhaMessage):
    """24312, a single club chat stream entry.

    The previous version read a module level `player` global, which does not
    exist in this codebase, and declared `encode(self)`, which Messaging cannot
    call. It also always re-sent the last row of a table nothing ever wrote to.
    """

    def __init__(self, messageData):
        super().__init__(messageData)
        self.messageVersion = 0

    def encode(self, fields, player=None):
        entry = fields.get("Entry")
        if entry:
            AllianceChat.encode_entry(self, entry)
        else:
            AllianceChat.encode_empty_entry(self)

    def decode(self):
        return {}

    def execute(self, *args, **kwargs):
        pass

    def getMessageType(self):
        return 24312

    def getMessageVersion(self):
        return self.messageVersion