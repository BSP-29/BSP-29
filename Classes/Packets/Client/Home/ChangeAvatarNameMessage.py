from Classes.Messaging import Messaging

from Classes.Packets.PiranhaMessage import PiranhaMessage


class ChangeAvatarNameMessage(PiranhaMessage):
    def __init__(self, messageData):
        super().__init__(messageData)
        self.messageVersion = 0

    def encode(self, fields):
        self.writeString(fields["Name"])
        self.writeBoolean(fields["NameSetByUser"])

    def decode(self):
        fields = {}
        fields["Name"] = self.readString()
        fields["NameSetByUser"] = self.readBoolean()
        super().decode(fields)
        return fields

    def execute(message, calling_instance, fields, cryptoInit):
        player = calling_instance.player
        new_name = fields["Name"]
        
        player.Name = new_name
        player.Registered = True
        
        player._db_dyn.set_name(new_name)
        player._db_dyn.set_registered(True)
        
        print(f"📝 Nome impostato via 10212: {new_name} per ID {player.LowID}")

        Messaging.sendMessage(24104, {
            "Socket": calling_instance.client,
            "Tick": 0,
            "ServerChecksum": 0,
            "ClientChecksum": 0
        }, cryptoInit, player)

    def getMessageType(self):
        return 10212

    def getMessageVersion(self):
        return self.messageVersion