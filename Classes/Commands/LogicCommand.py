import Configuration
from Classes.ByteStream import ByteStream
from Classes.Utility import Utility


class LogicCommand(ByteStream):
    def __init__(self, commandData):
        super().__init__(commandData)
        self.messageBuffer = commandData
        self.messagePayload = commandData

    def encode(self, fields):
        self.writeVInt(0)
        self.writeVInt(0)
        self.writeVLong(0, 0)

    def decode(calling_instance, fields, auto_decode=True):
        fields["TickWhenGiven"] = calling_instance.readVInt()
        fields["ExecuteTick"] = calling_instance.readVInt()
        # Consume the ExecutorAccountID VLong from the stream so the offset
        # stays aligned, but never trust the value the client sends (it is
        # always -1, -1). The real executor is resolved from the caller's
        # database in each command's execute() via player.LowID / player.ID.
        calling_instance.readVLong()
        fields["ExecutorAccountID"] = [0, 0]
        if Configuration.settings['PrintEnabled'] and auto_decode == True:
            Utility.parseFields(fields)
        return fields

    def parseFields(fields):
        if Configuration.settings['PrintEnabled']:
            Utility.parseFields(fields)
