from Classes.Packets.Client.Home.AvatarNameCheckResponseMessage import AvatarNameCheckResponseMessage
from Classes.Packets.PiranhaMessage import PiranhaMessage
from Classes.Messaging import Messaging
from Classes.ClientsManager import ClientsManager


class AvatarNameCheckRequestMessage(PiranhaMessage):
    def __init__(self, client, player=None):
        super().__init__(client)
        self.id = 14600
        self.messageVersion = 0
        self.player = player
        self.client = client
        self.name = ""

    def decode(self):
        fields = {}
        self.name = self.readString()
        print(f"New Name = {self.name}")
        fields["Name"] = self.name
        super().decode(fields)
        return fields

    def execute(self, calling_instance, fields, cryptoInit):
        fields["Name"] = self.name
        fields["Socket"] = calling_instance.client
        Messaging.sendMessage(20300, fields, cryptoInit, self.player)

    def getMessageType(self):
        return 14600

    def getMessageVersion(self):
        return self.messageVersion