from Classes.Packets.PiranhaMessage import PiranhaMessage

class LeaderboardMessage(PiranhaMessage):
    def __init__(self, messageData):
        super().__init__(messageData)
        self.id = 24403
        self.messageVersion = 0
        
        self.LeaderboardType = 1
        self.CharacterId = 0
        self.Avatars = []
        self.Brawlers = {}
        self.AllianceList = []
        self.OwnAvatarId = 0
        self.Region = ""

    def decode(self):
        return {}

    def encode(self, *args, **kwargs):
        playerIndex = 0
        
        fields = None
        player = None
        
        if 'fields' in kwargs:
            fields = kwargs.get('fields')
        if 'player' in kwargs:
            player = kwargs.get('player')
        
        if not fields:
            for arg in args:
                if isinstance(arg, dict):
                    fields = arg
                    break
        
        if not player:
            for arg in args:
                if hasattr(arg, 'LowID') or hasattr(arg, 'Name'):
                    player = arg
                    break
        
        if not fields:
            fields = {}
        
        self.LeaderboardType = fields.get("LeaderboardType", 1)
        self.CharacterId = fields.get("CharacterId", 0)
        self.Avatars = fields.get("Avatars", [])
        self.Brawlers = fields.get("Brawlers", {})
        self.AllianceList = fields.get("AllianceList", [])
        self.OwnAvatarId = fields.get("OwnAvatarId", 0)
        self.Region = fields.get("Region", "US")
        
        region = getattr(player, 'Region', self.Region) if player else self.Region
        bp_activated = getattr(player, 'bp_activated', True)
        
        # === HEADER ===
        self.writeVInt(self.LeaderboardType)
        self.writeVInt(2)
        self.writeDataReference(self.CharacterId, 0)
        self.writeString(region)
        
        # === TIPO 1: LEADERBOARD GIOCATORI ===
        if self.LeaderboardType == 1:
            self.writeVInt(len(self.Avatars))
            
            for index, (home, avatar) in enumerate(self.Avatars):
                if avatar.get("player_id", 0) == self.OwnAvatarId:
                    playerIndex = index + 1
                
                self.writeVLong(0, avatar.get("player_id", 0))
                self.writeVInt(1)
                self.writeVInt(avatar.get("trophies", 0))
                self.writeVInt(1)
                self.writeString(avatar.get("club_name", ""))
                self.writeString(avatar.get("name", "Brawler"))
                self.writeVInt(100)
                self.writeVInt(28000000 + avatar.get("thumbnail", 16))
                self.writeVInt(43000000 + avatar.get("namecolor", 0))
                
                if bp_activated:
                    self.writeVInt(43000000 + avatar.get("namecolor", 0))
                else:
                    self.writeVInt(0)
                
                self.writeVInt(0)
            
            self.writeVInt(0)
            
            check = False
            for index, (home, avatar) in enumerate(self.Avatars):
                if avatar.get("player_id", 0) == self.OwnAvatarId:
                    self.writeVInt(index + 1)
                    check = True
                    break
            
            if not check:
                self.writeVInt(0)
        
        # === TIPO 2: LEADERBOARD CLUB ===
        elif self.LeaderboardType == 2:
            self.writeVInt(len(self.AllianceList))
            
            for alliance in self.AllianceList:
                self.writeVLong(0, alliance.get("id", 0))
                self.writeVInt(1)
                self.writeVInt(alliance.get("trophies", 0))
                self.writeVInt(2)
                self.writeString(alliance.get("name", ""))
                self.writeVInt(alliance.get("member_count", 0))
                self.writeDataReference(8, alliance.get("badge_id", 0))
            
            self.writeVInt(0)
            
            check = False
            for index, alliance in enumerate(self.AllianceList):
                if alliance.get("id", 0) == self.OwnAvatarId:
                    self.writeVInt(index + 1)
                    check = True
                    break
            
            if not check:
                self.writeVInt(0)
        
        # === TIPO 0: LEADERBOARD BRAWLER ===
        elif self.LeaderboardType == 0:
            brawler_list = list(self.Brawlers.items())
            self.writeVInt(len(brawler_list))
            
            for index, (brawler_id, trophies) in enumerate(brawler_list):
                self.writeVLong(16, self.OwnAvatarId)
                self.writeVInt(1)
                self.writeVInt(trophies)
                self.writeVInt(1)
                self.writeString("")
                
                player_name = getattr(player, 'Name', 'Brawler') if player else "Brawler"
                self.writeString(player_name)
                
                self.writeVInt(100)
                thumbnail = getattr(player, 'Thumbnail', 16) if player else 16
                self.writeVInt(28000000 + thumbnail)
                namecolor = getattr(player, 'Namecolor', 0) if player else 0
                self.writeVInt(43000000 + namecolor)
                
                if bp_activated:
                    self.writeVInt(43000000 + namecolor)
                else:
                    self.writeVInt(0)
                
                self.writeVInt(0)
        
        # === TIPO 3: LEADERBOARD EVENTI ===
        elif self.LeaderboardType == 3:
            self.writeVInt(len(self.Avatars))
            
            for index, (home, avatar) in enumerate(self.Avatars):
                if avatar.get("player_id", 0) == self.OwnAvatarId:
                    playerIndex = index + 1
                
                self.writeVLong(0, avatar.get("player_id", 0))
                self.writeVInt(1)
                self.writeVInt(22)
                self.writeVInt(3)
                self.writeString(avatar.get("club_name", ""))
                self.writeString(avatar.get("name", "Brawler"))
                self.writeVInt(100)
                self.writeVInt(28000000 + avatar.get("thumbnail", 16))
                self.writeVInt(43000000 + avatar.get("namecolor", 0))
                
                if bp_activated:
                    self.writeVInt(43000000 + avatar.get("namecolor", 0))
                else:
                    self.writeVInt(0)
                
                self.writeVInt(0)
        
        else:
            self.writeVInt(0)
        
        # === FOOTER ===
        self.writeVInt(0)
        self.writeVInt(0)
        self.writeString(region)

    def execute(self, *args, **kwargs):
        pass

    def getMessageType(self):
        return self.id

    def getMessageVersion(self):
        return self.messageVersion