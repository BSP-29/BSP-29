from Classes.ByteStream import ByteStream

class ListBrawlTvChannelsMessage(ByteStream):

    def __init__(self, client, player=None):
        super().__init__(client)
        self.id = 24700
        self.messageVersion = 0
        self.client = client
        self.player = player

    def encode(self):
        self.writeVint(1) # count
        
        self.writeVint(1)
        self.writeString("BSP")
        self.writeString("By")
        self.writeString("LL|Leonikk44")

    def getMessageType(self):
        return 24700

    def getMessageVersion(self):
        return self.messageVersion
