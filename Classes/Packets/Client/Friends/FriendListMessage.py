from Classes.Packets.PiranhaMessage import PiranhaMessage
from Classes.DB.DynamicDB import DynamicDB as DB
import json
import os

class FriendListMessage(PiranhaMessage):
    def __init__(self, messageData):
        super().__init__(messageData)
        self.id = 20105
        self.messageVersion = 0

    def encode(self, fields, player):
        # === LEGGI DIRETTAMENTE DAL DB ===
        db_direct = DB(player_id=str(player.LowID))
        friends_list = db_direct.get_friends_list()
        
        # Se non ci sono amici, manda lista vuota
        if not friends_list:
            self.writeInt(0)
            self.writeBoolean(True)
            self.writeInt(0)
            return
        
        # === MOSTRA TUTTI GLI AMICI DEL PLAYER ===
        valid_friends = []
        for friend in friends_list:
            try:
                friend_id = int(friend.get("id", 0) or 0)
            except (AttributeError, TypeError, ValueError):
                continue
            # Old requests could leave a self-reference in the persisted list.
            if friend_id == int(player.LowID):
                continue

            # Ottieni i dati dell'amico dal suo DB
            friend_db = DB(player_id=str(friend_id))
            f_data = friend_db._load_raw()

            if f_data:
                # Calcola i trofei totali dell'amico
                brawler_trophies = f_data.get("BrawlerTrophies", {})
                try:
                    total_trophies = sum(int(value or 0) for value in brawler_trophies.values())
                except (AttributeError, TypeError, ValueError):
                    total_trophies = 0

                valid_friends.append({
                    'id': friend_id,
                    'state': friend.get('state', 0),
                    'name': f_data.get("Name", "Player"),
                    'trophies': total_trophies,
                    'thumbnail': 16,
                    'namecolor': f_data.get("Namecolor", 0),
                    'chroma': 460001 if f_data.get("Namecolor", 0) > 0 else 460001
                })

        # === CAMPIONI COME LA REPO ===
        self.writeInt(0)
        self.writeBoolean(True)
        self.writeInt(len(valid_friends))
        
        for friend in valid_friends:
            # ID come 2 Int
            self.writeInt(0)  # High ID
            self.writeInt(friend.get('id', 0))  # Low ID
            
            # 6 Stringhe vuote (social)
            for _ in range(6):
                self.writeString("")

            # Trophies
            self.writeInt(friend.get('trophies', 0))
            
            # State values match the v28 client: 2 = outgoing, 3 = incoming.
            # 4 = Accepted (amici confermati)
            try:
                state = int(friend.get('state', 0) or 0)
            except (TypeError, ValueError):
                state = 0
            
            print(f"[FriendList] {player.Name} -> friend {friend.get('name')}: state={state}")
            
            self.writeInt(state)
            
            # 3 writeInt(0)
            self.writeInt(0)
            self.writeInt(0)
            self.writeInt(0)

            # Is in a match
            self.writeBoolean(False)
            
            # Clan Name
            self.writeString("")
            
            # Clan Role
            self.writeInt(0)

            # Has Player Data flag
            self.writeBoolean(True)
            
            # Nome
            self.writeString(friend.get('name', "Player"))
            
            # Level
            self.writeVInt(100)
            
            # Thumbnail
            self.writeVInt(28000000 + friend.get('thumbnail', 0))
            
            # Name color
            self.writeVInt(43000000 + friend.get('namecolor', 0))
            
            # Chroma Name
            if friend.get('chroma', 460001) == 460001:
                self.writeVInt(43000000 + friend.get('namecolor', 0))
            else:
                self.writeVInt(0)

    def decode(self):
        return {}

    def getMessageType(self):
        return self.id

    def getMessageVersion(self):
        return self.messageVersion
