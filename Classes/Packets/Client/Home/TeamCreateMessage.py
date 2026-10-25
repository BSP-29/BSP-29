from Classes.Messaging import Messaging
from Classes.Packets.PiranhaMessage import PiranhaMessage
from Classes.TeamManager import create_room

class TeamCreateMessage(PiranhaMessage):
    def __init__(self, messageData):
        super().__init__(messageData)
        self.messageVersion = 0

    def encode(self, fields):
        pass

    def decode(self):
        fields = {}
        self.readVInt()
        fields["index"] = self.readVInt()
        fields["type"] = self.readVInt()
        super().decode(fields)
        return fields

    def execute(message, calling_instance, fields, cryptoInit):
        player = calling_instance.player

        room_type = fields["type"]
        room_high = 0

        # crea una room persistente con il tipo scelto dal proprietario
        room_id = create_room(player, room_type=room_type, room_high=room_high)

        print("[CREATE] room_id:", room_id, "TeamID:", player.TeamID)

        fields["Socket"] = calling_instance.client
        Messaging.sendMessage(24124, fields, cryptoInit, player)

    def getMessageType(self):
        return 14350

    def getMessageVersion(self):
        return self.messageVersion