from Classes.Packets.PiranhaMessage import PiranhaMessage


class MyAllianceMessage(PiranhaMessage):
    def __init__(self, messageData):
        super().__init__(messageData)
        self.messageVersion = 0

    def encode(self, fields, player):
        self.writeVInt(player.ClubOnlinePeople) # Online people in alliance
        self.writeBoolean(player.IsInAlliance) # isInAlliance
        self.writeDataReference(25, player.ClubRole)
        self.writeLong(0, 1) # alliance ID
        self.writeString(player.ClubName) # alliance name
        self.writeDataReference(8, player.ClubIcon) # alliance icon
        self.writeVInt(player.ClubType) # type
        self.writeVInt(player.ClubMemberCount) # member count
        self.writeVInt(player.ClubTrophies) # total trophies
        self.writeVInt(player.ClubMinimumJoinTrophies) # minimum trophies to enter
        self.writeDataReference(0) # unknown
        self.writeString(player.Region) # location
        self.writeVInt(3) # unknown
        self.writeBoolean(player.ClubFamilyFriendly) # isFamilyFriendly

    def decode(self):
        fields = {}
        super().decode(fields)
        return {}

    def execute(message, calling_instance, fields):
        pass

    def getMessageType(self):
        return 24399

    def getMessageVersion(self):
        return self.messageVersion