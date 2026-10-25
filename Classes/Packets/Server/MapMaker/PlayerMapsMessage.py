import sqlite3
from Classes.Packets.PiranhaMessage import PiranhaMessage

class PlayerMapsMessage(PiranhaMessage):
    def __init__(self, messageData):
        super().__init__(messageData)
        self.messageVersion = 0

    def encode(self, fields, player):
        # 1. Connessione al DB e recupero mappe per il player [0, 1]
        conn = sqlite3.connect('map_maker.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT map_id, map_name, layout_id, map_data 
            FROM player_maps 
            WHERE player_high = 0 AND player_low = 1
        ''')
        maps = cursor.fetchall()
        conn.close()

        # 2. Scrittura del numero di mappe (maps.Length)
        self.writeVInt(len(maps))

        # 3. Loop foreach(PlayerMap map in maps)
        for row in maps:
            map_id = row[0]
            map_name = row[1]
            layout_id = row[2]
            map_data = row[3] # Questi sono i byte compressi salvati prima

            # --- Inizio logica map.Encode(Stream) ---
            
            # ID Mappa (LogicLong: High + Low)
            self.writeVInt(0)      # High
            self.writeVInt(map_id) # Low
            
            self.writeString(map_name)
            self.writeVInt(0) # Stato della mappa (0 = Bozza/Draft)
            
            # DataReference per l'ambiente (Layout)
            self.writeVInt(15)      # ClassID (solitamente 15 per gli ambienti)
            self.writeVInt(layout_id) # InstanceID
            
            # Statistiche/Dati aggiuntivi (spesso 0 nei server privati)
            self.writeVInt(0) # Win count
            self.writeVInt(0) # Loss count
            self.writeVInt(0) # Draw count
            
            # Scrittura dei dati dei blocchi (MapData)
            if map_data is not None:
                # writeBytes emits its own Int32 length prefix, so the extra
                # writeVInt(len) above duplicated it with a different width and
                # the call itself was missing the required length argument.
                self.writeBytes(map_data, len(map_data))
            else:
                self.writeVInt(0) # Mappa vuota
            
            self.writeVInt(0) # VInt extra (solitamente versioning della mappa)
            # --- Fine logica map.Encode ---

    def decode(self):
        return {}

    def getMessageType(self):
        return 22102

    def getMessageVersion(self):
        return self.messageVersion