import json
import random
import string
from typing import Optional
from Classes.DB.DynamicDB import DynamicDB as DB
from Classes.DB.AllianceDB import AllianceDatabase
from Classes.DB.ChatDB import ChatDB


class Player:
    def __init__(self, low_id=0):
        self.HighID = 0
        self.LowID = low_id
        self.ID = [self.HighID, self.LowID]
        self.DemoAccount = 0
        self._db_dyn = DB(player_id=str(self.LowID))
        
        # Database per Alliance e Chat
        self.alliance_db = AllianceDatabase()
        self.chat_db = ChatDB()
        
        # Initialize ClubLowID BEFORE _load_alliance_data()
        self.ClubLowID = 0
        
        # Dati dal DynamicDB
        self.Token = self._db_dyn.get_token()
        self.Namecolor = self._db_dyn.get_name_color()
        self.DnDState = self._db_dyn.get_dnd_state()
        self.TeamChatMuted = self._db_dyn.get_team_chat_muted()
        self.ThemeID = self._db_dyn.get_theme_id()
        self.UnlockedBrawlers = {}
        self.UnlockedSkins = {}
        self.Region = self._db_dyn.get_region()
        self.QuestSeen = self._db_dyn.get_quest_seen()
        self.GadgetStatus = self._db_dyn.get_gadget_status()
        self.Name = self._db_dyn.get_name()
        self.Registered = self._db_dyn.get_registered()
        print(f"[Player.__init__] Namecolor = {self.Namecolor}")
        
        # === CARICA IL BRAWLER SELEZIONATO E I SUOI TROFEI DAL DB ===
        self.SelectedBrawler = self._db_dyn.get_selected_brawler()
        self.BrawlerTrophies = self._db_dyn.get_brawler_trophies(self.SelectedBrawler)
        
        # === ORA CALCOLA I TROFEI TOTALI DAL DB (somma di tutti i brawler) ===
        total_trophies = self._db_dyn.get_total_trophies()
        self.Trophies = total_trophies if total_trophies > 0 else 0
        self.HighestTrophies = self.Trophies
        
        # VIP GRADES:
        self.Bronze = self._db_dyn.get_bronze()
        self.Silver = self._db_dyn.get_silver()
        self.Ruby = self._db_dyn.get_ruby()
        self.Rainbow = self._db_dyn.get_rainbow()
        self.RainbowX = self._db_dyn.get_rainbow_x()
        
        self.ClientVersion = "0.0.0"
        self.DemoAccount = 0
        self.Thumbnail = 16
        self.ContentCreator = "LL|Leonikk44"
        team_membership = self._db_dyn.get_team_membership()
        self.TeamID = team_membership["TeamID"]
        self.TeamType = team_membership["TeamType"]
        self.TeamOwnerID = team_membership["TeamOwnerID"]
        self.TeamIsOwner = team_membership["TeamIsOwner"]
        self.TeamMapID = team_membership["TeamMapID"]
        
        # MODIFICATO: Gems e Coins letti dal DB invece che hardcoded
        self.Coins = self._db_dyn.get_coins()
        self.Gems = self._db_dyn.get_gems()
        
        self.Elixir = 999999
        self.Chips = 999999
        self.PowerPlayPoints = 999999
        self.PowerPoints = 999999
        
        # Dati Alliance (caricati dal AllianceDatabase)
        self._load_alliance_data()
        self.Wins = 0 # Unused Actually
        self.TeamStarPower = 0
        self.TeamGadget = 0
        self.SelectedStarPowers = self._db_dyn.get_selected_star_powers()
        self.SelectedGadgets = self._db_dyn.get_selected_gadgets()
        
        self.StarPoints = self._db_dyn.get_star_points()
        self.TrophyRoadTier = 600
        self.Experience = 999999
        self.Level = 444
        self.TeamPraticeStatus = False
        self.Tokens = 200
        self.Boxes = 0
        self.TrophyLoss = 750
        self.TokensDoubler = self._db_dyn.get_tokens_doubler()
        
        self.ClubTrophiesNeed = 0
        self.NameChangeCost = 0
        self.NameChangeTimer = 0
        self.ClubDescription = "BSP = Brawl Stars Projects - This is v29 - Server by LL|Leonikk44"
        self.CityRampage = 16
        self.ChallengeWins = 1000
        self.ThreeVThree = 1000
        self.PowerLeaguePoints = 999999
        self.BattleTokenDoubled = 500
        self.Boss = 16
        self.Kaiju = self.CityRampage
        self.NotificationReadStatus = False
        self.RoboRumble = 16
        self.SoloWins = 1000
        self.EquippedCards = self._db_dyn.get_equipped_cards()
        self.DuoWins = 1000
        self.PowerLeagueLeaderboardsPlace = 1
        self.PLLP = self.PowerLeagueLeaderboardsPlace
        self.OffOnStatus = 2
        self.LastTimeSeen = 0
        self.ClubMinimumJoinTrophies = 0
        self.ClubIcon = 0
        self.session = None
        self.ClubWar = False
        self.ClubMemberCount = 1
        self.ClubRole = 1
        self.ClubType = 3
        self.ProfileDescription = "hello world"
        self.IsInAlliance = True
        self.ClubOnlinePeople = 1
        self.ClubFamilyFriendly = True
        self.FamilyFriendly = True
        self.RankedTrophies = 125
        self.Tickets = 999999
        self.BrawlerLevel = 8
        self.TutorialState = 2
        self.ChatStatus = True
        self.ClubTrophies = self.Trophies * self.ClubMemberCount
        self.ChromaNameStatus = 4600001
        self.BattleQuestWin = 1
        self.TokenOfferPrice = 20
        self.TokenOfferQuantity = 100
        self.BigBoxPrice = 50
        self.MegaBoxPrice = 100
        self.BattleQuestType = 1
        self.BattleQuestXP = 2000
        
        # ---- Battle Rewards ----
        self.StarPlayerPoints = 104
        self.VictoryPoints = 67
        self.TrophiesRewarded = 0
        self.StarPointsRewarded = 0
        self.PPTrophiesRewarded = 0
        self.TokensRewarded = 0
        self.BattleResultTokens = 2000
        self.RoomLowID = 1
        self.TeamBPL = 10
        self.isReady = False

        self.SelectedMap = 1
        self.SelectedSkins = {}

        # Rebuild persistent team membership when this account reconnects after a restart.
        from Classes.TeamManager import restore_player_team
        restore_player_team(self)
    
    # === METODI PER LA GESTIONE DEI TROFEI (USANO SOLO IL DB) ===
    
    def get_brawler_trophies(self, brawler_id: int) -> int:
        """Ottiene i trofei per un brawler specifico dal DB"""
        return self._db_dyn.get_brawler_trophies(brawler_id)

    def set_brawler_trophies(self, brawler_id: int, trophies: int) -> None:
        """Imposta i trofei per un brawler specifico nel DB e aggiorna i totali"""
        self._db_dyn.set_brawler_trophies(brawler_id, trophies)
        
        # Se è il brawler corrente, aggiorna anche BrawlerTrophies in RAM
        if brawler_id == self.SelectedBrawler:
            self.BrawlerTrophies = trophies
        
        # Aggiorna i trofei totali dal DB
        self.update_total_trophies()

    def get_all_brawlers_trophies(self) -> dict:
        """Ottiene i trofei di tutti i brawler dal DB"""
        return self._db_dyn.get_all_brawlers_trophies()

    def add_brawler_trophies(self, brawler_id: int, amount: int) -> int:
        """Aggiunge trofei a un brawler nel DB e restituisce il nuovo valore"""
        new_trophies = self._db_dyn.add_brawler_trophies(brawler_id, amount)
        
        # Se è il brawler corrente, aggiorna anche BrawlerTrophies in RAM
        if brawler_id == self.SelectedBrawler:
            self.BrawlerTrophies = new_trophies
        
        # Aggiorna i trofei totali dal DB
        self.update_total_trophies()
        
        return new_trophies

    def load_brawler_trophies(self) -> None:
        """Carica i trofei del brawler selezionato dal DB"""
        self.BrawlerTrophies = self._db_dyn.get_brawler_trophies(self.SelectedBrawler)

    def switch_brawler(self, brawler_id: int) -> None:
        """Cambia brawler e carica i suoi trofei dal DB"""
        # Cambia brawler
        self.SelectedBrawler = brawler_id
        self._db_dyn.set_selected_brawler(brawler_id)
        
        # Carica i trofei del nuovo brawler dal DB
        self.BrawlerTrophies = self._db_dyn.get_brawler_trophies(brawler_id)
        print(f"[Player] Switched to brawler {brawler_id} with {self.BrawlerTrophies} trophies")

    def sync_brawler_trophies(self) -> None:
        """Sincronizza i trofei del brawler corrente nel DB"""
        self._db_dyn.set_brawler_trophies(self.SelectedBrawler, self.BrawlerTrophies)
        
        # Aggiorna i totali
        self.update_total_trophies()

    def get_total_trophies(self) -> int:
        """Ottiene il totale dei trofei di tutti i brawler dal DB"""
        return self._db_dyn.get_total_trophies()

    def get_top_brawler(self) -> Optional[int]:
        """Ottiene il brawler con più trofei dal DB"""
        return self._db_dyn.get_top_brawler()

    def get_brawler_rank(self, brawler_id: int) -> int:
        """Ottiene la posizione in classifica di un brawler dal DB"""
        return self._db_dyn.get_brawler_rank(brawler_id)

    def update_total_trophies(self) -> None:
        """Aggiorna self.Trophies e self.HighestTrophies dal DB"""
        total = self._db_dyn.get_total_trophies()
        self.Trophies = total if total > 0 else 0
        if self.Trophies > self.HighestTrophies:
            self.HighestTrophies = self.Trophies
        # Aggiorna anche i trofei del club
        self.ClubTrophies = self.Trophies * self.ClubMemberCount

    # === METODI PER L'ALLIANCE ===

    def _load_alliance_data(self):
        """Carica i dati dell'alliance dal AllianceDatabase"""
        if self.LowID == 0:
            self.ClubLowID = 0
            self.ClubName = "BSP by LL|Leonikk44"
            self.ClubDescription = "BSP = Brawl Stars Projects - This is v29 - Server by LL|Leonikk44"
            self.ClubMemberCount = 1
            self.ClubRole = 1
            self.ClubType = 3
            self.ClubTrophies = 0
            self.ClubTrophiesNeed = 0
            self.ClubMinimumJoinTrophies = 0
            self.ClubFamilyFriendly = True
            self.FamilyFriendly = True
            self.ClubOnlinePeople = 1
            self.IsInAlliance = False
            return
        
        alliance_data = self.alliance_db.getPlayerAlliance(self.LowID)
        
        if alliance_data:
            self.ClubLowID = alliance_data.get("id", 0)
            self.ClubName = alliance_data.get("name", "")
            self.ClubDescription = alliance_data.get("description", "")
            self.ClubMemberCount = alliance_data.get("member_count", 1)
            self.ClubType = alliance_data.get("type", 1)
            self.ClubTrophies = alliance_data.get("trophies", 0)
            self.ClubTrophiesNeed = alliance_data.get("trophies_needed", 0)
            self.ClubMinimumJoinTrophies = alliance_data.get("min_join_trophies", 0)
            self.ClubFamilyFriendly = alliance_data.get("friendly_family", True)
            self.FamilyFriendly = self.ClubFamilyFriendly
            self.Region = self.Region
            self.IsInAlliance = True
            
            member_data = self.alliance_db.getMember(self.LowID, self.ClubLowID)
            if member_data:
                self.ClubRole = member_data.get("club_role", 1)
            else:
                self.ClubRole = 1
            
            self.ClubOnlinePeople = self.ClubMemberCount
        else:
            self.ClubLowID = 0
            self.ClubName = "BSP by LL|Leonikk44"
            self.ClubDescription = "BSP = Brawl Stars Projects - This is v29 - Server by LL|Leonikk44"
            self.ClubMemberCount = 1
            self.ClubRole = 1
            self.ClubType = 3
            self.ClubTrophies = 0
            self.ClubTrophiesNeed = 0
            self.ClubMinimumJoinTrophies = 0
            self.ClubFamilyFriendly = True
            self.FamilyFriendly = True
            self.ClubOnlinePeople = 1
            self.IsInAlliance = False
    
    def load_alliance(self):
        """Ricarica i dati dell'alliance dal database"""
        self._load_alliance_data()
    
    def create_alliance(self, name=None, description=None, type=None, 
                        min_trophies=None, family_friendly=None):
        """Crea una nuova alliance per il player"""
        if self.LowID == 0:
            return None
        
        alliance_name = name if name else self.ClubName
        alliance_desc = description if description else self.ClubDescription
        alliance_type = type if type else self.ClubType
        min_join = min_trophies if min_trophies else self.ClubMinimumJoinTrophies
        friendly = family_friendly if family_friendly else self.ClubFamilyFriendly
        
        alliance_id = self.alliance_db.createAlliance(
            player=self,
            name=alliance_name,
            description=alliance_desc,
            type=alliance_type,
            trophies_needed=min_join,
            friendly_family=friendly
        )
        
        if alliance_id:
            self.ClubLowID = alliance_id
            self.load_alliance()
            print(f"[Player] Created alliance: {alliance_name} (ID: {alliance_id})")
            return alliance_id
        
        return None
    
    def join_alliance(self, alliance_id):
        """Unisce il player a un alliance esistente"""
        if self.LowID == 0:
            return False
        
        alliance_data = self.alliance_db.getAlliance(alliance_id)
        if not alliance_data:
            return False
        
        if self.IsInAlliance and self.ClubLowID:
            self.alliance_db.removeMember(self.LowID, self.ClubLowID)
        
        success = self.alliance_db.addMember(self.LowID, alliance_id, self.ClubRole)
        
        if success:
            self.ClubLowID = alliance_id
            self.load_alliance()
            print(f"[Player] Joined alliance: {alliance_data['name']} (ID: {alliance_id})")
            return True
        
        return False
    
    def leave_alliance(self):
        """Lascia l'alliance corrente"""
        if not self.IsInAlliance or not self.ClubLowID:
            return False
        
        success = self.alliance_db.removeMember(self.LowID, self.ClubLowID)
        
        if success:
            self.ClubLowID = 0
            self.ClubName = "BSP by LL|Leonikk44"
            self.ClubDescription = "BSP = Brawl Stars Projects - This is v29 - Server by LL|Leonikk44"
            self.ClubMemberCount = 1
            self.ClubRole = 1
            self.ClubType = 3
            self.ClubTrophies = 0
            self.ClubTrophiesNeed = 0
            self.ClubMinimumJoinTrophies = 0
            self.ClubFamilyFriendly = False
            self.FamilyFriendly = False
            self.ClubOnlinePeople = 0
            self.IsInAlliance = False
            
            print(f"[Player] Left alliance: {self.ClubName}")
            return True
        
        return False
    
    def add_chat_message(self, player_name, player_role, event_type, tick, message=""):
        """Aggiunge un messaggio alla chat dell'alliance"""
        if not self.IsInAlliance or not self.ClubLowID:
            return None
        
        return self.chat_db.addMessage(
            club_id=self.ClubLowID,
            player_id=self.LowID,
            player_name=player_name,
            player_role=player_role,
            event_type=event_type,
            tick=tick,
            message=message
        )
    
    def get_chat_messages(self, limit=100):
        """Recupera i messaggi della chat dell'alliance"""
        if not self.IsInAlliance or not self.ClubLowID:
            return []
        
        return self.chat_db.getMessages(self.ClubLowID, limit)
    
    def get_chat_message_count(self):
        """Recupera il conteggio dei messaggi della chat"""
        if not self.IsInAlliance or not self.ClubLowID:
            return 0
        
        return self.chat_db.getMessageCount(self.ClubLowID)
    
    def update_alliance(self, **kwargs):
        """Aggiorna i dati dell'alliance corrente"""
        if not self.IsInAlliance or not self.ClubLowID:
            return False
        
        return self.alliance_db.updateAlliance(self.ClubLowID, **kwargs)
    
    def close_databases(self):
        """Chiude tutte le connessioni ai database"""
        self.alliance_db.close()
        self.chat_db.close()

    # === METODI PER LA GESTIONE DELL'ACCOUNT ===

    def create_new_player(self):
        creation_manager = DB("0")
        new_id, new_token = creation_manager.create_account()
        
        self.LowID = int(new_id)
        self.ID = [self.HighID, self.LowID]
        self.Token = new_token
        
        self._db_dyn = DB(player_id=str(self.LowID))
        self.alliance_db = AllianceDatabase()
        self.chat_db = ChatDB()
        
        print(f"[Player] New account created into the DB: ID {self.LowID}")
        return self.LowID, self.Token

    def load_from_db(self):
        """Ricarica tutti i dati dal database"""
        self.Token = self._db_dyn.get_token()
        self.Namecolor = self._db_dyn.get_name_color()
        self.DnDState = self._db_dyn.get_dnd_state()
        self.TeamChatMuted = self._db_dyn.get_team_chat_muted()
        self.ThemeID = self._db_dyn.get_theme_id()
        self.Region = self._db_dyn.get_region()
        self.QuestSeen = self._db_dyn.get_quest_seen()
        self.GadgetStatus = self._db_dyn.get_gadget_status()
        self.Name = self._db_dyn.get_name()
        self.Registered = self._db_dyn.get_registered()
        self.SelectedBrawler = self._db_dyn.get_selected_brawler()
        self.BrawlerTrophies = self._db_dyn.get_brawler_trophies(self.SelectedBrawler)
        
        # MODIFICATO: Ricarica Gems e Coins dal DB
        self.Gems = self._db_dyn.get_gems()
        self.Coins = self._db_dyn.get_coins()
        
        self.update_total_trophies()
        self.load_alliance()
        print(f"[Player] Loaded from DB: {self.Name} (ID: {self.LowID})")

    def update_db(self):
        """Salva tutti i dati nel database"""
        self._db_dyn.set_name_color(self.Namecolor)
        self._db_dyn.set_dnd_state(self.DnDState)
        self._db_dyn.set_team_chat_muted(self.TeamChatMuted)
        self._db_dyn.set_theme_id(self.ThemeID)
        self._db_dyn.set_region(self.Region)
        self._db_dyn.set_quest_seen(self.QuestSeen)
        self._db_dyn.set_gadget_status(self.GadgetStatus)
        self._db_dyn.set_name(self.Name)
        self._db_dyn.set_registered(self.Registered)
        self._db_dyn.set_selected_brawler(self.SelectedBrawler)
        
        # Salva i trofei del brawler corrente nel DB
        self._db_dyn.set_brawler_trophies(self.SelectedBrawler, self.BrawlerTrophies)
        
        # MODIFICATO: Salva Gems e Coins nel DB
        self._db_dyn.set_gems(self.Gems)
        self._db_dyn.set_coins(self.Coins)
        self._db_dyn.set_star_points(self.StarPoints)
        self._db_dyn.set_tokens_doubler(self.TokensDoubler)

    # Aggiungi a Player.py, dopo load_from_db o prima di toJSON

    def update_last_active(self) -> None:
        """Aggiorna il timestamp dell'ultima attività del giocatore"""
        self._db_dyn.update_last_active()

    def is_online(self, timeout_seconds: int = 300) -> bool:
        """Verifica se il giocatore è online"""
        return self._db_dyn.is_online(timeout_seconds)

    def get_last_active_str(self) -> str:
        """Restituisce il tempo trascorso dall'ultima attività"""
        return self._db_dyn.get_last_active_str()

    def toJSON(self):
        data = self.__dict__.copy()
        if "_db_dyn" in data:
            del data["_db_dyn"]
        if "alliance_db" in data:
            del data["alliance_db"]
        if "chat_db" in data:
            del data["chat_db"]
        return data