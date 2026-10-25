import sqlite3
from Classes.Packets.PiranhaMessage import PiranhaMessage

class DeletePlayerMapMessage(PiranhaMessage):
    def __init__(self, messageData):
        super().__init__(messageData)

    def decode(self):
        self.fields = {}
        self.readVInt() # High
        self.fields["MapId"] = self.readVInt() # Low
        return self.fields

    def execute(self, player, fields):
        conn = sqlite3.connect('map_maker.db')
        cursor = conn.cursor()
        try:
            cursor.execute('DELETE FROM player_maps WHERE map_id = ? AND player_low = 1', (fields["MapId"],))
            conn.commit()
            print(f"[MapMaker] Eliminata mappa ID: {fields['MapId']}")
        finally:
            conn.close()

    def getMessageType(self):
        return 12101