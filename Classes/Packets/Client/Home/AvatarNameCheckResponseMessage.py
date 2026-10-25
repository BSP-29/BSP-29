from Classes.ByteStream import ByteStream
from Classes.Messaging import Messaging
from Classes.Packets.PiranhaMessage import PiranhaMessage

class AvatarNameCheckResponseMessage(PiranhaMessage):

    def __init__(self, client, player=None, name=None):
        super().__init__(client)
        self.messageVersion = 0
        self.id = 20300
        self.player = player
        self.name = name

    def encode(self, fields):
        
        chosen_name = "Brawler"
        
        if self.name:
            chosen_name = self.name
        elif isinstance(fields, dict):
            if "Name" in fields:
                chosen_name = fields["Name"]
            elif "name" in fields:
                chosen_name = fields["name"]

        self.writeVInt(0)
        self.writeInt(0)
        self.writeString(chosen_name)
        print(f"Name Verified! The New Name is {chosen_name}")

    def getMessageType(self):
        return 20300

    def getMessageVersion(self):
        return self.messageVersion