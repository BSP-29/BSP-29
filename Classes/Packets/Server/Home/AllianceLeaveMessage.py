from Classes.DB.AllianceDB import AllianceDatabase
from Classes.Messaging import Messaging
from Classes.Packets.PiranhaMessage import PiranhaMessage
import time

class AllianceLeaveMessage(PiranhaMessage):

    def __init__(self, messageData):
        super().__init__(messageData)
        self.id = 14308
        self.messageVersion = 0

    def decode(self):
        fields = {}
        # Nessun campo da leggere (payload vuoto)
        super().decode(fields)
        return fields

    def execute(self, calling_instance, fields, cryptoInit):
        if fields is None:
            fields = {}
        
        fields["Socket"] = calling_instance.client
        player = calling_instance.player
        
        clubLowID = getattr(player, 'ClubLowID', getattr(player, 'low_id', 0))
        
        if clubLowID == 0:
            print(f"[AllianceLeaveMessage] ERROR: Player {player.Name} not in any club")
            fields["errorCode"] = 1
            Messaging.sendMessage(24333, fields, cryptoInit)
            return
        
        member_data = player.alliance_db.getMember(player.LowID, clubLowID)
        
        if member_data is None:
            print(f"[AllianceLeaveMessage] ERROR: Player not in club {clubLowID}")
            fields["errorCode"] = 1
            Messaging.sendMessage(24333, fields, cryptoInit)
            return
        
        success = player.alliance_db.removeMember(player.LowID, clubLowID)
        
        if not success:
            print(f"[AllianceLeaveMessage] ERROR: Failed to remove player from club {clubLowID}")
            fields["errorCode"] = 2
            Messaging.sendMessage(24333, fields, cryptoInit)
            return
        
        player.ClubLowID = 0
        player.ClubHighID = 0
        player.ClubRole = 0
        
        print(f"[AllianceLeaveMessage] SUCCESS: Player {player.Name} left club {clubLowID}")
        fields["errorCode"] = 0
        Messaging.sendMessage(24333, fields, cryptoInit)
        print("Waiting 1 Second before sending OutOfSync...") 
        time.sleep(1)
        Messaging.sendMessage(
            24104,
            {
                "Socket":  calling_instance.client,
                "ServerChecksum": 0,
                "ClientChecksum": 0,
                "Tick": 0
            },
            cryptoInit,
            player)


    def encode(self, fields):
        errorCode = fields.get("errorCode", 0)
        self.writeVInt(errorCode)

    def getMessageType(self):
        return self.id

    def getMessageVersion(self):
        return self.messageVersion