import sqlite3
from Classes.Messaging import Messaging
from Classes.Packets.PiranhaMessage import PiranhaMessage


class UpdatePlayerMapMessage(PiranhaMessage):
    def __init__(self, messageData):
        super().__init__(messageData)
        self.messageVersion = 0

    def decode(self):
        self.fields = {}
        # LogicLong MapID (High + Low)
        self.readVInt()  # High
        self.fields["MapId"] = self.readVInt()  # Low

        length = self.readVInt()
        # readBytes caps at 1000 bytes by default and silently returns b"" past
        # it, so real maps were persisted empty while the handler reported OK.
        self.fields["MapData"] = self.readBytes(length, 0xFFFFFF)
        return self.fields

    def execute(message, calling_instance, fields, cryptoInit):
        conn = sqlite3.connect('map_maker.db')
        cursor = conn.cursor()

        error_code = 0
        try:
            cursor.execute('''
                UPDATE player_maps 
                SET map_data = ? 
                WHERE map_id = ? AND player_low = 1
            ''', (fields["MapData"], fields["MapId"]))
            conn.commit()
        except Exception as e:
            error_code = 1
            print(f"[UpdatePlayerMap DB Error] {e}")
        finally:
            conn.close()

        # Player has no sendNetMessage, so route the acknowledgement through
        # Messaging, which is what every other client handler does.
        fields["errorCode"] = error_code
        fields["mapId"] = fields["MapId"]
        fields["Socket"] = calling_instance.client
        Messaging.sendMessage(
            22103,
            fields,
            cryptoInit,
            getattr(calling_instance, "player", None),
        )

    def getMessageType(self):
        return 12103

    def getMessageVersion(self):
        return self.messageVersion