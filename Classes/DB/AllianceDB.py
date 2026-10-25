import sqlite3
import os
from Classes.DB.DynamicDB import DynamicDB as DB


class AllianceDatabase:
    """Database separato SQLite per gestire Alliance/Club"""
    
    def __init__(self, db_path="database/alliances.db"):
        """Inizializza il database"""
        self.db_path = db_path
        self.conn = None
        self.connect()
        self.create_tables()
    
    def connect(self):
        """Connette al database SQLite"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
    
    def create_tables(self):
        """Crea le tabelle se non esistono"""
        cursor = self.conn.cursor()
        
        # Tabella principale per Alliance/Club
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alliance (
                id INTEGER PRIMARY KEY,
                high_id INTEGER DEFAULT 0,
                name TEXT NOT NULL,
                badge_id INTEGER DEFAULT 0,
                member_count INTEGER DEFAULT 0,
                type INTEGER DEFAULT 3,
                trophies INTEGER DEFAULT 0,
                trophies_needed INTEGER DEFAULT 0,
                region TEXT DEFAULT 'IT',
                friendly_family INTEGER DEFAULT 1,
                description TEXT DEFAULT '',
                min_join_trophies INTEGER DEFAULT 0,
                icon INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabella per i membri dell'alliance
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alliance_member (
                player_id INTEGER PRIMARY KEY,
                alliance_id INTEGER NOT NULL,
                club_role INTEGER DEFAULT 1,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (alliance_id) REFERENCES alliance(id),
                UNIQUE(player_id, alliance_id)
            )
        """)
        
        # Tabella per la storia dei trofei
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alliance_trophy_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alliance_id INTEGER NOT NULL,
                trophies_change INTEGER NOT NULL,
                reason TEXT DEFAULT '',
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (alliance_id) REFERENCES alliance(id)
            )
        """)
        
        self.conn.commit()
    
    # ==================== ALLANCE - CREAZIONE ====================
    
    def createAlliance(self, player):
        """Crea una nuova alliance basata sui dati del player"""
        cursor = self.conn.cursor()
        
        # Usa i dati dal player
        name = player.ClubName if player.ClubName else "New Alliance"
        badge_id = player.ClubIcon if player.ClubIcon else 0
        type = player.ClubType if player.ClubType else 3
        region = player.Region if player.Region else "IT"
        trophies_needed = player.ClubMinimumJoinTrophies if player.ClubMinimumJoinTrophies else 0
        friendly_family = 1 if player.ClubFamilyFriendly else 0
        description = player.ClubDescription if player.ClubDescription else ""
        member_count = player.ClubMemberCount if player.ClubMemberCount else 1
        trophies = player.ClubTrophies if player.ClubTrophies else 0
        
        cursor.execute("""
            INSERT INTO alliance (name, badge_id, type, region, trophies_needed, 
                                  friendly_family, description, member_count, trophies)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, badge_id, type, region, trophies_needed, 
              friendly_family, description, member_count, trophies))
        
        alliance_id = cursor.lastrowid
        
        # Aggiungi il player come primo membro (presidente)
        self.addMember(player.LowID, alliance_id, 2)  # 2 = President
        
        self.conn.commit()
        return alliance_id
    
    # ==================== ALLANCE - LEGGERE ====================
    
    def getAlliance(self, alliance_id):
        """Recupera tutti i dati di un alliance"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT id, high_id, name, badge_id, member_count, type, 
                   trophies, trophies_needed, region, friendly_family, 
                   description, min_join_trophies, icon, created_at, updated_at
            FROM alliance
            WHERE id = ?
        """, (alliance_id,))
        
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None
    
    def getAllianceByName(self, name):
        """Recupera alliance per nome"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT id, high_id, name, badge_id, member_count, type, 
                   trophies, trophies_needed, region, friendly_family
            FROM alliance
            WHERE name = ?
        """, (name,))
        
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None
    
    def getAllAlliances(self):
        """Recupera tutte le alliance"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT id, high_id, name, badge_id, member_count, type, 
                   trophies, trophies_needed, region, friendly_family
            FROM alliance
            ORDER BY trophies DESC
        """)
        
        return [dict(row) for row in cursor.fetchall()]
    
    def getPlayerAlliance(self, player_id):
        """Recupera l'alliance di un player specifico"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT a.id, a.high_id, a.name, a.badge_id, a.member_count, a.type, 
                   a.trophies, a.trophies_needed, a.region, a.friendly_family,
                   a.description, a.min_join_trophies, a.icon
            FROM alliance a
            INNER JOIN alliance_member m ON a.id = m.alliance_id
            WHERE m.player_id = ?
        """, (player_id,))
        
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None
    
    # ==================== ALLANCE - UPDATE ====================
    
    def updateAlliance(self, alliance_id, **kwargs):
        """Aggiorna i dati di un alliance"""
        cursor = self.conn.cursor()
        
        updates = []
        params = []
        
        for key, value in kwargs.items():
            if value is not None:
                db_key = self._map_player_key(key)
                updates.append(f"{db_key} = ?")
                params.append(value)
        
        if not updates:
            return False
        
        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(alliance_id)
        
        query = f"UPDATE alliance SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, params)
        self.conn.commit()
        
        return cursor.rowcount > 0
    
    def _map_player_key(self, player_key):
        """Mappa i nomi delle chiavi del Player ai nomi del database"""
        mapping = {
            'ClubName': 'name',
            'ClubIcon': 'badge_id',
            'ClubType': 'type',
            'Region': 'region',
            'ClubMinimumJoinTrophies': 'trophies_needed',
            'ClubFamilyFriendly': 'friendly_family',
            'ClubDescription': 'description',
            'ClubMemberCount': 'member_count',
            'ClubTrophies': 'trophies',
            'name': 'name',
            'badge_id': 'badge_id',
            'type': 'type',
            'region': 'region',
            'trophies_needed': 'trophies_needed',
            'friendly_family': 'friendly_family',
            'description': 'description',
            'member_count': 'member_count',
            'trophies': 'trophies'
        }
        return mapping.get(player_key, player_key)
    
    def updateMemberCount(self, alliance_id, member_count):
        """Aggiorna il conteggio membri"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            UPDATE alliance 
            SET member_count = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (member_count, alliance_id))
        
        self.conn.commit()
        return cursor.rowcount > 0
    
    def updateTrophies(self, alliance_id, trophies):
        """Aggiorna i trofei totali"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            UPDATE alliance 
            SET trophies = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (trophies, alliance_id))
        
        self.conn.commit()
        return cursor.rowcount > 0
    
    def addTrophies(self, alliance_id, trophies_change, reason=""):
        """Aggiunge/rimuove trofei e registra nella storia"""
        cursor = self.conn.cursor()
        
        # Recupera trofei attuali
        cursor.execute("SELECT trophies FROM alliance WHERE id = ?", (alliance_id,))
        row = cursor.fetchone()
        if not row:
            return False
        
        current_trophies = row[0]
        new_trophies = current_trophies + trophies_change
        
        # Aggiorna trofei
        cursor.execute("""
            UPDATE alliance 
            SET trophies = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (new_trophies, alliance_id))
        
        # Registra nella storia
        cursor.execute("""
            INSERT INTO alliance_trophy_history (alliance_id, trophies_change, reason)
            VALUES (?, ?, ?)
        """, (alliance_id, trophies_change, reason))
        
        self.conn.commit()
        return new_trophies
    
    # ==================== ALLANCE - DELETE ====================
    
    def deleteAlliance(self, alliance_id):
        """Elimina un alliance e tutti i suoi membri"""
        cursor = self.conn.cursor()
        
        # Elimina membri
        cursor.execute("DELETE FROM alliance_member WHERE alliance_id = ?", (alliance_id,))
        
        # Elimina storia trofei
        cursor.execute("DELETE FROM alliance_trophy_history WHERE alliance_id = ?", (alliance_id,))
        
        # Elimina alliance
        cursor.execute("DELETE FROM alliance WHERE id = ?", (alliance_id,))
        
        self.conn.commit()
        return cursor.rowcount > 0
    
    # ==================== MEMBRI - ADD ====================
    
    def addMember(self, player_id, alliance_id, club_role=1):
        """Aggiunge un membro all'alliance"""
        cursor = self.conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO alliance_member (player_id, alliance_id, club_role)
                VALUES (?, ?, ?)
            """, (player_id, alliance_id, club_role))
            
            # Aggiorna conteggio membri
            cursor.execute("SELECT member_count FROM alliance WHERE id = ?", (alliance_id,))
            row = cursor.fetchone()
            if row:
                new_count = row[0] + 1
                cursor.execute("""
                    UPDATE alliance SET member_count = ? WHERE id = ?
                """, (new_count, alliance_id))
            
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
    
    # ==================== MEMBRI - REMOVE ====================
    
    def removeMember(self, player_id, alliance_id):
        """Rimuove un membro dall'alliance"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            DELETE FROM alliance_member 
            WHERE player_id = ? AND alliance_id = ?
        """, (player_id, alliance_id))
        
        # Aggiorna conteggio membri
        cursor.execute("SELECT member_count FROM alliance WHERE id = ?", (alliance_id,))
        row = cursor.fetchone()
        if row and row[0] > 0:
            new_count = row[0] - 1
            cursor.execute("""
                UPDATE alliance SET member_count = ? WHERE id = ?
            """, (new_count, alliance_id))
        
        self.conn.commit()
        return cursor.rowcount > 0
    
    # ==================== MEMBRI - GET ====================
    
    def getMembers(self, alliance_id):
        """Recupera tutti i membri di un alliance con dati completi dal DynamicDB"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT player_id, alliance_id, club_role, joined_at
            FROM alliance_member
            WHERE alliance_id = ?
        """, (alliance_id,))
        
        members_raw = [dict(row) for row in cursor.fetchall()]
        
        # Aggiungi dati dal DynamicDB per ogni membro
        members = []
        for member in members_raw:
            player_id = member["player_id"]
            member_db = DB(player_id=str(player_id))
            
            # Aggiungi dati completi al dict del membro
            member["name"] = member_db.get_name()
            member["trophies"] = member_db.get_trophies() if hasattr(member_db, 'get_trophies') else 999999
            member["experience"] = member_db.get_experience() if hasattr(member_db, 'get_experience') else 0
            member["thumbnail"] = member_db.Thumbnail if hasattr(member_db, 'Thumbnail') else 16
            member["namecolor"] = member_db.get_name_color()
            
            members.append(member)
        
        return members
    
    def getMember(self, player_id, alliance_id):
        """Recupera un membro specifico"""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT player_id, alliance_id, club_role, joined_at
            FROM alliance_member
            WHERE player_id = ? AND alliance_id = ?
        """, (player_id, alliance_id))
        
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None
    
    # ==================== UTILITY ====================
    
    def close(self):
        """Chiude la connessione al database"""
        if self.conn:
            self.conn.close()
    
    def __enter__(self):
        """Per l'uso con 'with'"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Chiude automaticamente al termine"""
        self.close()