from Classes.Packets.PiranhaMessage import PiranhaMessage

class GetLeaderboardMessage(PiranhaMessage):
    def __init__(self, messageData):
        super().__init__(messageData)
        self.id = 14403
        self.messageVersion = 0
        
        self.IsRegional = False
        self.LeaderboardType = 0
        self.CharacterId = 0

    def decode(self):
        self.IsRegional = self.readBoolean()
        self.LeaderboardType = self.readVInt()
        self.CharacterId = self.readDataReference()
        
        self.IsRegional = False
        return {
            "IsRegional": self.IsRegional,
            "LeaderboardType": self.LeaderboardType,
            "CharacterId": self.CharacterId
        }

    def encode(self, *args, **kwargs):
        pass

    def execute(self, *args, **kwargs):
        from Classes.Messaging import Messaging
        from Classes.DB.DynamicDB import DynamicDB as DB
        from Classes.DB.AllianceDB import AllianceDatabase
        import glob
        import json
        import os
        
        # Estrai parametri
        fields = None
        cryptoInit = None
        player = None
        calling_instance = None
        
        if 'fields' in kwargs:
            fields = kwargs.get('fields')
        if 'cryptoInit' in kwargs:
            cryptoInit = kwargs.get('cryptoInit')
        if 'player' in kwargs:
            player = kwargs.get('player')
        if 'calling_instance' in kwargs:
            calling_instance = kwargs.get('calling_instance')
        
        if not fields:
            for arg in args:
                if isinstance(arg, dict):
                    fields = arg
                    break
        
        if not cryptoInit:
            for arg in args:
                if hasattr(arg, 'player') or hasattr(arg, 'crypto') or hasattr(arg, 'encryptServer'):
                    cryptoInit = arg
                    if hasattr(arg, 'player'):
                        player = arg.player
                    break
        
        if not player and cryptoInit:
            player = getattr(cryptoInit, 'player', None)
        
        if not fields:
            print("[Leaderboard] No fields found")
            return
        
        if not cryptoInit:
            print("[Leaderboard] No cryptoInit found")
            return
        
        if player is None:
            print("[Leaderboard] No player found")
            return
        
        leaderboard_type = fields.get("LeaderboardType", 1)
        character_id = fields.get("CharacterId", 0)
        
        alliance_db = AllianceDatabase()
        
        avatars = []
        brawlers = {}
        alliances = []
        
        # === TIPO 1: LEADERBOARD GIOCATORI ===
        if leaderboard_type == 1:
            pattern = os.path.join("data/dynamic", "0-*.json")
            players_data = []
            
            for path in glob.glob(pattern):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    
                    filename = os.path.basename(path)
                    low_id = int(filename.split("-")[1].replace(".json", ""))
                    
                    brawler_trophies = data.get("BrawlerTrophies", {})
                    total_trophies = sum(brawler_trophies.values())
                    
                    club_data = alliance_db.getPlayerAlliance(low_id)
                    club_name = club_data.get("name", "") if club_data else ""
                    
                    players_data.append({
                        "player_id": low_id,
                        "name": data.get("Name", "Brawler"),
                        "trophies": total_trophies,
                        "thumbnail": 16,
                        "namecolor": data.get("Namecolor", 0),
                        "club_name": club_name
                    })
                except Exception:
                    continue
            
            players_data.sort(key=lambda x: x["trophies"], reverse=True)
            players_data = players_data[:100]
            avatars = [(p, p) for p in players_data]
        
        # === TIPO 2: LEADERBOARD CLUB ===
        elif leaderboard_type == 2:
            alliances = alliance_db.getAllAlliances()
            
            for alliance in alliances:
                club_id = alliance.get("id")
                members = alliance_db.getMembers(club_id)
                
                real_trophies = 0
                for member in members:
                    member_id = member.get("player_id")
                    try:
                        member_db = DB(player_id=str(member_id))
                        member_trophies = member_db.get_total_trophies()
                        real_trophies += member_trophies
                    except Exception:
                        real_trophies += member.get("trophies", 0)
                
                alliance["trophies"] = real_trophies
            
            alliances.sort(key=lambda x: x.get("trophies", 0), reverse=True)
            alliances = alliances[:100]
        
        # === TIPO 0: LEADERBOARD BRAWLER ===
        elif leaderboard_type == 0:
            all_brawlers = {}
            pattern = os.path.join("data/dynamic", "0-*.json")
            
            for path in glob.glob(pattern):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    
                    brawler_trophies = data.get("BrawlerTrophies", {})
                    for brawler_id, trophies in brawler_trophies.items():
                        b_id = int(brawler_id)
                        if b_id not in all_brawlers:
                            all_brawlers[b_id] = 0
                        all_brawlers[b_id] += trophies
                except Exception:
                    continue
            
            sorted_brawlers = sorted(all_brawlers.items(), key=lambda x: x[1], reverse=True)
            sorted_brawlers = sorted_brawlers[:100]
            brawlers = dict(sorted_brawlers)
        
        # === TIPO 3: LEADERBOARD EVENTI ===
        elif leaderboard_type == 3:
            pattern = os.path.join("data/dynamic", "0-*.json")
            players_data = []
            
            for path in glob.glob(pattern):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    
                    filename = os.path.basename(path)
                    low_id = int(filename.split("-")[1].replace(".json", ""))
                    
                    club_data = alliance_db.getPlayerAlliance(low_id)
                    club_name = club_data.get("name", "") if club_data else ""
                    
                    players_data.append({
                        "player_id": low_id,
                        "name": data.get("Name", "Brawler"),
                        "trophies": 22,
                        "thumbnail": 16,
                        "namecolor": data.get("Namecolor", 0),
                        "club_name": club_name
                    })
                except Exception:
                    continue
            
            players_data = players_data[:100]
            avatars = [(p, p) for p in players_data]
        
        alliance_db.close()
        
        fields_response = {
            "LeaderboardType": leaderboard_type,
            "CharacterId": character_id if not isinstance(character_id, list) else (character_id[1] if len(character_id) > 1 else 0),
            "Avatars": avatars,
            "Brawlers": brawlers,
            "AllianceList": alliances,
            "OwnAvatarId": player.LowID,
            "Region": getattr(player, 'Region', 'US'),
            "player": player
        }
        
        # PASSIAMO cryptoInit DIRETTAMENTE - Messaging si occuperà di estrarre il crypto
        Messaging.sendMessage(24403, fields_response, cryptoInit, player, calling_instance)

    def getMessageType(self):
        return self.id

    def getMessageVersion(self):
        return self.messageVersion