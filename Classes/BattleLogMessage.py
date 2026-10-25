from Classes.ByteStream import ByteStream
from Classes.ClientsManager import ClientsManager
from Classes.Packets.PiranhaMessage import PiranhaMessage
from Classes.Logic.LogicLong import LogicLong

class BattleLogMessage(PiranhaMessage):

    def __init__(self, messageData):
        super().__init__(messageData)
        self.messageVersion = 0
        

    def encode(self, fields, player):
        self.writeBoolean(True)

        self.writeVInt(1) # Count: exactly one entry is written below

        self.writeVInt(0)
        self.writeVInt(0)    # Time When Battle Log Entry Was Created
        self.writeVInt(1)    # Battle Log Type (1 = Normal, 2 = Crash, 3 = Survived for <time>, 
        self.writeVInt(6)    # Trophies Result
        self.writeVInt(120)  # Battle Time
        self.writeInt(0)   # Type [0 = Power Play, 1 = Friendly, 2 = Championship]
        self.writeDataReference(15, 95) # Map SCID
        self.writeVInt(2) # Victory/Defeat/Draw
        self.writeVInt(0) # ???

        self.writeInt(0)
        self.writeInt(0)

        self.writeVInt(1)
        self.writeInt(1)

        self.writeVInt(0)  # array

        self.writeVInt(0)
        self.writeInt(0)
        self.writeVInt(0)
        self.writeInt(0)
        self.writeVInt(0)

        print("[INFO] Message BattleLogMessage has been sent.")

    def decode(self):
        pass

    def getMessageType(self):
        return 23458

    def getMessageVersion(self):
        return self.messageVersion