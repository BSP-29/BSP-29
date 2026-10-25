from Classes.Messaging import Messaging
from Classes.Packets.PiranhaMessage import PiranhaMessage


class AskForAllianceDataMessage(PiranhaMessage):
    def __init__(self, messageData):
        super().__init__(messageData)
        self.messageVersion = 0
        self.id = 14302
        # Initialize attributes
        self.clubHighID = 0
        self.clubLowID = 0

    def decode(self):
        fields = {}
        
        # Leggi TUTTI i campi nel buffer (9 VInt totali)
        field0 = self.readVInt()  # VInt[0] = 0
        field1 = self.readVInt()  # VInt[1] = 0
        field2 = self.readVInt()  # VInt[2] = 0
        field3 = self.readVInt()  # VInt[3] = 0
        field4 = self.readVInt()  # VInt[4] = 0
        field5 = self.readVInt()  # VInt[5] = 0
        field6 = self.readVInt()  # VInt[6] = 0
        self.clubLowID = self.readVInt()  # VInt[7] = 1 ← CLUB LOW ID!
        field8 = self.readVInt()  # VInt[8] = 0
        
        # Stampa tutti i fields per debug
        print(f"[AskForAllianceDataMessage] field0: {field0}")
        print(f"[AskForAllianceDataMessage] field1: {field1}")
        print(f"[AskForAllianceDataMessage] field2: {field2}")
        print(f"[AskForAllianceDataMessage] field3: {field3}")
        print(f"[AskForAllianceDataMessage] field4: {field4}")
        print(f"[AskForAllianceDataMessage] field5: {field5}")
        print(f"[AskForAllianceDataMessage] field6: {field6}")
        print(f"[AskForAllianceDataMessage] clubLowID: {self.clubLowID}")
        print(f"[AskForAllianceDataMessage] field8: {field8}")
        print(f"[AskForAllianceDataMessage] All fields: {fields}")
        
        super().decode(fields)
        
        return fields

    def execute(self, calling_instance, fields, cryptoInit):
        # Inizializza fields se è None
        if fields is None:
            fields = {}
        
        fields["Socket"] = calling_instance.client
        player = calling_instance.player
        
        # Usa clubLowID dal decode
        clubLowID = self.clubLowID
        
        print(f"[AskForAllianceDataMessage] Sending AllianceDataMessage for clubLowID: {clubLowID}")
        
        # Passa clubLowID a AllianceDataMessage tramite fields
        fields["clubLowID"] = clubLowID
        Messaging.sendMessage(24301, fields, cryptoInit, player, calling_instance)

    def encode(self, fields):
        pass

    def getMessageType(self):
        return self.id

    def getMessageVersion(self):
        return self.messageVersion