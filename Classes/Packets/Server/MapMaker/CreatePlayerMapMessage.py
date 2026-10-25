import sqlite3
from Classes.Packets.PiranhaMessage import PiranhaMessage

class CreatePlayerMapMessage(PiranhaMessage):
    def __init__(self, messageData):
        super().__init__(messageData)

    def decode(self):
        self.fields = {}
        self.fields["MapName"] = self.readString()
        self.fields["GMV"] = self.readVInt()
        # DataReference: ClassID e InstanceID (Layout)
        self.readVInt() # ClassID (solitamente ignorato)
        self.fields["LayoutInstanceID"] = self.readVInt() 
        return self.fields

    def execute(self, player, fields):
        conn = sqlite3.connect('map_maker.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS player_maps (
                map_id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_high INTEGER DEFAULT 0,
                player_low INTEGER DEFAULT 1,
                map_name TEXT,
                layout_id INTEGER,
                map_data BLOB
            )
        ''')

        try:
            cursor.execute('''
                INSERT INTO player_maps (player_high, player_low, map_name, layout_id) 
                VALUES (?, ?, ?, ?)
            ''', (0, 1, fields["MapName"], fields["LayoutInstanceID"]))
            conn.commit()
            print(f"[MapMaker] Creata mappa: {fields['MapName']}")
        except Exception as e:
            print(f"[DB Error] {e}")
        finally:
            conn.close()

    def getMessageType(self):
        return 12100