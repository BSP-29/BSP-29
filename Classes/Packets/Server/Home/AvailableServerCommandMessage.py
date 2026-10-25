from Classes.Logic.LogicCommandManager import LogicCommandManager
from Classes.Packets.PiranhaMessage import PiranhaMessage

from Classes.Logic.RewardDelivery import build_delivery


class AvailableServerCommandMessage(PiranhaMessage):
    """24111, a server side command.

    The command's own encode writes its command id as the first field, which
    is what the v29 client reads. This message used to write the id itself as
    well, so the id appeared twice and everything after it was shifted by a
    field.

    Callers that already have the payload from RewardDelivery.build_delivery
    pass it in Payload and the command is not run a second time.
    """

    def __init__(self, messageData):
        super().__init__(messageData)
        self.messageVersion = 0
        self.player = None  # filled in by Messaging when it passes the player

    def encode(self, fields, player=None):
        active_player = player if player else self.player
        command_id = int(fields.get("Command", {}).get("ID", 0) or 0)

        payload = fields.get("Payload")
        if payload is not None:
            # Already rendered, including the command id.
            self.messagePayload += bytes(payload)
            self.offset += len(payload)
            return self.messagePayload

        # Otherwise run the command, which writes the id itself.
        command = LogicCommandManager.createCommand(
            command_id, self.messagePayload, active_player
        )
        if command:
            command.encode(fields)
            # The command was handed this message's buffer as its own, but
            # bytes += rebinds rather than mutates, so the result has to be
            # taken back off the command or the payload ends up empty.
            self.messagePayload = command.messagePayload
            self.offset = command.offset
        return self.messagePayload

    def decode(self):
        return {}

    def getMessageType(self):
        return 24111