from random import choice
from Classes.ByteStreamHelper import ByteStreamHelper
from Classes.Packets.PiranhaMessage import PiranhaMessage
from Classes.ChronosTextEntry import ChronosTextEntry
from Classes.Files.Classes.Characters import Characters
from Classes.Files.Classes.Skins import Skins
from Classes.Files.Classes.Cards import Cards
from Classes.Files.Classes.Emotes import Emotes
from Classes.Files.Classes.Locations import Locations

class OwnHomeDataMessage(PiranhaMessage):
    def __init__(self, messageData):
        super().__init__(messageData)
        self.messageVersion = 0

    def encode(self, fields, player):
        self.player = player
        skins = Skins.getSkinsID()
        brawlers = Characters.getBrawlersID()
        brawlersUnlockID = Cards.getBrawlersUnlockID()
        gadgets = Cards.getGadgetsID()
        starPowers = Cards.getStarpowersID()
        emotes = Emotes.getEmotesID()
        locations = Locations.getAllMaps()
        
        selected_brawler = player.SelectedBrawler
        
        # === OTTIENI I TROFEI DI TUTTI I BRAWLER DIRETTAMENTE DAL DB ===
        brawler_trophies_list = []
        for brawler_id in range(120):
            trophies = player._db_dyn.get_brawler_trophies(brawler_id)
            brawler_trophies_list.append({
                "id": brawler_id,
                "trophies": trophies
            })
        
        # === DEBUG ===
        print(f"\n{'='*60}")
        print(f"[Home] Selected brawler: {selected_brawler}")
        print(f"[Home] Brawlers with trophies > 0:")
        has_trophies = False
        for b in brawler_trophies_list:
            if b["trophies"] > 0:
                print(f"  ✅ Brawler {b['id']}: {b['trophies']} trophies")
                has_trophies = True
        if not has_trophies:
            print(f"  ⚠️ No brawlers with trophies > 0 in DB")
        print(f"{'='*60}\n")
        
        # === CONTINUA CON IL RESTO DEL MESSAGGIO ===
        self.writeVInt(2026 * 1000 + 0)
        self.writeVInt(0)
        self.writeVInt(player.Trophies)
        self.writeVInt(player.HighestTrophies)
        self.writeVInt(player.RankedTrophies)
        self.writeVInt(player.TrophyRoadTier)
        self.writeVInt(player.Experience)
        self.writeDataReference(28, player.Thumbnail)
        self.writeDataReference(43, player.Namecolor)
        
        # Played Game Modes Array
        self.writeVInt(20)
        for x in range(20):
            self.writeVInt(x)

        # Selected Skins Array
        self.writeVInt(len(player.SelectedSkins))
        for x in player.SelectedSkins.values():
            self.writeDataReference(29, x)

        # Unlocked Skins Array
        self.writeVInt(len(skins))
        for x in skins:
            self.writeDataReference(29, x)
        
        self.writeVInt(len(player.SelectedStarPowers) + len(player.SelectedGadgets))
        for x in list(player.SelectedStarPowers.values()) + list(player.SelectedGadgets.values()):
            self.writeDataReference(23, x)
        
        self.writeVInt(0)
        self.writeVInt(player.HighestTrophies)
        self.writeVInt(0)
        self.writeVInt(0)
        self.writeBoolean(True)
        self.writeVInt(player.TokensDoubler)
        self.writeVInt(2721626)
        self.writeVInt(0)
        self.writeVInt(2268712)
        
        self.writeVInt(0)
        self.writeVInt(0)
        self.writeVInt(0)
        for x in range(0):
            self.writeVInt(0)
        
        self.writeBoolean(False)
        self.writeBoolean(False)
        self.writeBoolean(False)
        self.writeBoolean(True)
        self.writeVInt(2)
        self.writeVInt(2)
        self.writeVInt(2)
        self.writeVInt(player.NameChangeCost)
        self.writeVInt(player.NameChangeTimer)
        
        # Shop Array
        from Classes.Logic.Shop import Shop
        try:
            Shop.EncodeShopOffers(self)
        except Exception as e:
            print(f"[OHD] Shop.EncodeShopOffers failed: {e}")
            self.writeVInt(0)
        # Shop Array End

        self.writeVInt(1)
        for x in range (1):
            self.writeVInt(0)
            self.writeVInt(0)
            self.writeVInt(10)
        # Brawl Box Ads Array End
        self.writeVInt(player.Tokens)
        self.writeVInt(0)
        self.writeVInt(0)
        self.writeVInt(player.Tickets)
        self.writeVInt(0)
        self.writeDataReference(16, player.SelectedBrawler)
        self.writeString(player.Region)
        self.writeString(player.ContentCreator)

        self.writeVInt(7)
        self.writeInt(3)
        self.writeInt(player.TokensRewarded)
        self.writeInt(4)
        self.writeInt(player.TrophiesRewarded)
        self.writeInt(6)
        self.writeInt(player.DemoAccount)
        self.writeInt(7)
        self.writeInt(player.DnDState)
        self.writeInt(8)
        self.writeInt(player.StarPointsRewarded)
        self.writeInt(9)
        self.writeInt(1)
        self.writeInt(10)
        self.writeInt(player.PPTrophiesRewarded)
        
        self.writeVInt(0)
        for x in range(0):
            self.writeVInt(0)
            self.writeDataReference(16, 0)
            self.writeVInt(0)

        self.writeVInt(1)

        # === BRAWL PASS SEASON DATA (Dynamic from DB) ===
        current_season = 2  # Season 3 (0-indexed)
        season_end_timestamp = 34500  # Far future placeholder
        has_premium = player._db_dyn.get_brawl_pass_bought()
        pass_tokens = player._db_dyn.get_brawl_pass_tokens()
        
        self.writeVInt(current_season)           # Season ID
        self.writeVInt(pass_tokens)              # Pass tokens (Pro tokens)
        self.writeBoolean(has_premium)           # Has Brawl Pass (premium)
        self.writeVInt(pass_tokens)              # Pass tokens again
        self.writeBoolean(True)                  # Always True
        
        # Premium claimed tiers - 4 ints (split bitmask)
        premium_claimed = player._db_dyn.get_brawl_pass_claimed_split(True, current_season)
        for part in premium_claimed:
            self.writeInt(part)
        
        self.writeBoolean(True)                  # Always True
        
        # Free claimed tiers - 4 ints (split bitmask)
        free_claimed = player._db_dyn.get_brawl_pass_claimed_split(False, current_season)
        for part in free_claimed:
            self.writeInt(part)
            
        self.writeVInt(1)
        for x in range(1):
            self.writeVInt(1)
            self.writeVInt(0)
            
        self.writeBoolean(True)
        self.writeVInt(4)

        self.writeVInt(123456)
        self.writeVInt(2)
        self.writeVInt(1)
        self.writeVInt(9)
        self.writeVInt(10)
        self.writeVInt(2000)
        self.writeVInt(123456)
        self.writeVInt(0)
        self.writeVInt(0)
        self.writeVInt(1)
        self.writeBoolean(False)
        self.writeBoolean(player.QuestSeen)
        self.writeDataReference(16, 0)
        self.writeVInt(5)
        self.writeVInt(123456)
        self.writeVInt(123456)

        self.writeVInt(123456)
        self.writeVInt(2)
        self.writeVInt(1)
        self.writeVInt(9)
        self.writeVInt(10)
        self.writeVInt(2000)
        self.writeVInt(123456)
        self.writeVInt(0)
        self.writeVInt(0)
        self.writeVInt(1)
        self.writeBoolean(False)
        self.writeBoolean(player.QuestSeen)
        self.writeDataReference(16, 11)
        self.writeVInt(0)
        self.writeVInt(123456)
        self.writeVInt(123456)

        self.writeVInt(123456)
        self.writeVInt(2)
        self.writeVInt(1)
        self.writeVInt(99)
        self.writeVInt(100)
        self.writeVInt(2000)
        self.writeVInt(123456)
        self.writeVInt(0)
        self.writeVInt(0)
        self.writeVInt(0)
        self.writeBoolean(False)
        self.writeBoolean(player.QuestSeen)
        self.writeDataReference(16, 8)
        self.writeVInt(3)
        self.writeVInt(123456)
        self.writeVInt(123456)

        self.writeVInt(123456)
        self.writeVInt(2)
        self.writeVInt(1)
        self.writeVInt(99)
        self.writeVInt(100)
        self.writeVInt(4000)
        self.writeVInt(123456)
        self.writeVInt(0)
        self.writeVInt(0)
        self.writeVInt(0)
        self.writeBoolean(True)
        self.writeBoolean(player.QuestSeen)
        self.writeDataReference(16, 31)
        self.writeVInt(2)
        self.writeVInt(123456)
        self.writeVInt(123456)
        
        self.writeBoolean(True)
        self.writeVInt(len(emotes))
        for x in emotes:
            self.writeDataReference(52, x)
            self.writeVInt(0)

        self.writeVInt(2026 * 1000 + 0)
        self.writeVInt(100)
        self.writeVInt(10)
        self.writeVInt(player.BigBoxPrice)
        self.writeVInt(10)
        self.writeVInt(player.MegaBoxPrice)
        self.writeVInt(player.TokensDoubler)
        self.writeVInt(player.TokenOfferPrice)
        self.writeVInt(player.TokenOfferQuantity)
        
        # === USA I TROFEI DEL BRAWLER SELEZIONATO DAL DB ===
        selected_trophies = player._db_dyn.get_brawler_trophies(selected_brawler)
        self.writeVInt(selected_trophies)
        
        self.writeVInt(123456)
        self.writeVInt(123456)
        ByteStreamHelper.encodeIntList(self, [0, 30, 80, 170, 350, 0])

        # Event Slots Array
        self.writeVInt(100)
        for x in range(100):
            self.writeVInt(x + 1)

        # Logic Events Array
        self.writeVInt(8)

        self.writeVInt(1)
        self.writeVInt(1)
        self.writeVInt(0)
        self.writeVInt(356118)
        self.writeVInt(10)
        self.writeDataReference(15, 122)
        self.writeBoolean(True)
        self.writeBoolean(True)
        self.writeString()
        self.writeVInt(0)
        self.writeVInt(0)
        self.writeVInt(3)
        modifiers = [1]
        self.writeVInt(len(modifiers))
        for x in modifiers:
            self.writeVInt(x)
        self.writeVInt(0)
        self.writeVInt(0)

        self.writeVInt(2)
        self.writeVInt(2)
        self.writeVInt(0)
        self.writeVInt(356118)
        self.writeVInt(10)
        self.writeDataReference(15, 224)
        self.writeBoolean(True)
        self.writeBoolean(True)
        self.writeString()
        self.writeVInt(0)
        self.writeVInt(0)
        self.writeVInt(3)
        modifiers = [1]
        self.writeVInt(len(modifiers))
        for x in modifiers:
            self.writeVInt(x)
        self.writeVInt(0)
        self.writeVInt(0)

        self.writeVInt(5)
        self.writeVInt(5)
        self.writeVInt(0)
        self.writeVInt(356118)
        self.writeVInt(10)
        self.writeDataReference(15, 225)
        self.writeBoolean(True)
        self.writeBoolean(True)
        self.writeString()
        self.writeVInt(0)
        self.writeVInt(0)
        self.writeVInt(3)
        modifiers = [1]
        self.writeVInt(len(modifiers))
        for x in modifiers:
            self.writeVInt(x)
        self.writeVInt(0)
        self.writeVInt(0)

        self.writeVInt(3)
        self.writeVInt(3)
        self.writeVInt(0)
        self.writeVInt(356118)
        self.writeVInt(10)
        self.writeDataReference(15, 292)
        self.writeBoolean(True)
        self.writeBoolean(True)
        self.writeString()
        self.writeVInt(0)
        self.writeVInt(0)
        self.writeVInt(3)
        modifiers = [1]
        self.writeVInt(len(modifiers))
        for x in modifiers:
            self.writeVInt(x)
        self.writeVInt(0)
        self.writeVInt(0)

        self.writeVInt(6)
        self.writeVInt(6)
        self.writeVInt(0)
        self.writeVInt(356118)
        self.writeVInt(10)
        self.writeDataReference(15, 1)
        self.writeBoolean(True)
        self.writeBoolean(True)
        self.writeString()
        self.writeVInt(0)
        self.writeVInt(0)
        self.writeVInt(3)
        modifiers = [1]
        self.writeVInt(len(modifiers))
        for x in modifiers:
            self.writeVInt(x)
        self.writeVInt(0)
        self.writeVInt(0)

        self.writeVInt(4)
        self.writeVInt(4)
        self.writeVInt(0)
        self.writeVInt(356118)
        self.writeVInt(10)
        self.writeDataReference(15, 132)
        self.writeBoolean(True)
        self.writeBoolean(True)
        self.writeString()
        self.writeVInt(0)
        self.writeVInt(0)
        self.writeVInt(3)
        modifiers = [1]
        self.writeVInt(len(modifiers))
        for x in modifiers:
            self.writeVInt(x)
        self.writeVInt(0)
        self.writeVInt(0)

        self.writeVInt(7)
        self.writeVInt(7)
        self.writeVInt(0)
        self.writeVInt(356118)
        self.writeVInt(10)
        self.writeDataReference(15, 53)
        self.writeBoolean(True)
        self.writeBoolean(True)
        self.writeString()
        self.writeVInt(0)
        self.writeVInt(0)
        self.writeVInt(3)
        modifiers = [1]
        self.writeVInt(len(modifiers))
        for x in modifiers:
            self.writeVInt(x)
        self.writeVInt(0)
        self.writeVInt(0)

        self.writeVInt(19)
        self.writeVInt(19)
        self.writeVInt(0)
        self.writeVInt(356118)
        self.writeVInt(10)
        self.writeDataReference(15, 262)
        self.writeBoolean(True)
        self.writeBoolean(True)
        self.writeString()
        self.writeVInt(0)
        self.writeVInt(0)
        self.writeVInt(3)
        modifiers = [1]
        self.writeVInt(len(modifiers))
        for x in modifiers:
            self.writeVInt(x)
        self.writeVInt(0)
        self.writeVInt(0)

        # Coming Up Events Array
        self.writeVInt(0)

        ByteStreamHelper.encodeIntList(self, [20, 35, 75, 140, 290, 480, 800, 1250])
        ByteStreamHelper.encodeIntList(self, [1, 2, 3, 4, 5, 10, 15, 20])
        ByteStreamHelper.encodeIntList(self, [10, 30, 80])
        ByteStreamHelper.encodeIntList(self, [6, 20, 60])
        ByteStreamHelper.encodeIntList(self, [20, 50, 140, 280])
        ByteStreamHelper.encodeIntList(self, [150, 400, 1200, 2500])

        self.writeVInt(6)
        self.writeVInt(player.Tokens)
        self.writeVInt(20)
        self.writeVInt(0)
        self.writeVInt(10)
        self.writeVInt(5)
        self.writeBoolean(False)
        self.writeBoolean(False)
        self.writeBoolean(False)
        self.writeVInt(0)
        self.writeVInt(0)
        self.writeBoolean(False)
        self.writeVInt(0)
        self.writeVInt(1)
        self.writeInt(1)
        self.writeInt(player.ThemeID)
        
        self.writeVInt(0)
        self.writeVInt(0)
        self.writeLong(0, player.LowID)

        self.writeVInt(2)

        # Notification 81 - Welcome to BSP
        self.writeVInt(81)
        self.writeInt(3)
        self.writeBoolean(player.NotificationReadStatus)
        self.writeInt(0)
        self.writeString(f"<cff0000>W<cff4000>E<cff8000>L<cffc000>C<cffff00>O<cbfff00>M<c80ff00>E <c40ff00>T<c00ff00>O <c00ff80>B<c00ffff>S<c0080ff>P <c0000ff>\n<c00ffff>Server by LL|Leonikk44!</c>\n- t.me/BrawlStarsProjects")
        self.writeVInt(0)

        # Notification 81 - AVVISO ROSSO
        self.writeVInt(81)
        self.writeInt(1)
        self.writeBoolean(False)
        self.writeInt(0)
        self.writeString(f"<cff0000>DON'T USE GUEST ACCOUNTS!</c> <cff0000>(GUEST AND GUEST-2)</c> <cff0000>PLAY ON YOUR OWN ACCOUNT</c> <cff0000>USING BSP ID (Supercell ID)</c> <cff0000>AND IGNORE ANY</c> <cff0000>ERRORS</c> <cff0000>BY CLICKING OK</c>\n<c00ffff>Server by LL|Leonikk44!</c>\n- t.me/BrawlStarsProjects")
        self.writeVInt(0)

        self.writeVInt(0)
        self.writeBoolean(False)
        self.writeVInt(0)
        self.writeVInt(0)

        # === LOGIC CLIENT AVATAR ===
        self.writeVLong(0, player.LowID)
        self.writeVLong(0, 0)
        self.writeVLong(0, 0)
        self.writeString(player.Name)
        self.writeBoolean(player.Registered)
        self.writeInt(player.ChromaNameStatus)
        self.writeVInt(player.ChromaNameStatus)

        # Unlocked Brawler and Resources Array
        self.writeVInt(len(brawlersUnlockID) + 6)
        for hero in brawlersUnlockID:
            self.writeDataReference(23, hero)
            self.writeVInt(1)

        self.writeDataReference(5, 1)
        self.writeVInt(player.Boxes)
        self.writeDataReference(5, 5)
        self.writeVInt(player.Chips)
        self.writeDataReference(5, 6)
        self.writeVInt(player.Elixir)
        self.writeDataReference(5, 7)
        self.writeVInt(player.PowerPoints)
        self.writeDataReference(5, 8)
        self.writeVInt(player.Coins)
        self.writeDataReference(5, 10)
        self.writeVInt(player.StarPoints)

        # === BRAWLERS TROPHIES ARRAY (DAL DB) ===
        self.writeVInt(len(brawler_trophies_list))
        for brawler_data in brawler_trophies_list:
            self.writeDataReference(16, brawler_data["id"])
            self.writeVInt(brawler_data["trophies"])

        # === BRAWLERS HIGHEST TROPHIES ARRAY (DAL DB) ===
        self.writeVInt(len(brawler_trophies_list))
        for brawler_data in brawler_trophies_list:
            self.writeDataReference(16, brawler_data["id"])
            self.writeVInt(brawler_data["trophies"])

        # Highest Resources Amount Array
        self.writeVInt(0)
        for x in range(0):
            self.writeDataReference(5, 0)
            self.writeVInt(0)

        # Brawlers Power Points Array
        self.writeVInt(len(brawler_trophies_list))
        for brawler_data in brawler_trophies_list:
            self.writeDataReference(16, brawler_data["id"])
            self.writeVInt(player.PowerPoints)

        # Brawlers Level Array
        self.writeVInt(len(brawler_trophies_list))
        for brawler_data in brawler_trophies_list:
            self.writeDataReference(16, brawler_data["id"])
            self.writeVInt(player.BrawlerLevel)

        # Brawlers Star Power Array
        self.writeVInt(len(starPowers) + len(gadgets))
        for x in starPowers + gadgets:
            self.writeDataReference(23, x)
            self.writeVInt(1)

        # Brawlers Seem State Array
        self.writeVInt(len(brawler_trophies_list))
        for brawler_data in brawler_trophies_list:
            self.writeDataReference(16, 0)
            self.writeVInt(0)

        self.writeVInt(player.Gems)
        self.writeVInt(player.Gems)
        self.writeVInt(1)
        self.writeVInt(0)
        self.writeVInt(0)
        self.writeVInt(0)
        self.writeVInt(0)
        self.writeVInt(0)
        self.writeVInt(0)
        self.writeVInt(0)
        self.writeVInt(player.TutorialState)
        self.writeVInt(2)

    def decode(self):
        fields = {}
        fields["AccountID"] = self.readLong()
        fields["HomeID"] = self.readLong()
        fields["PassToken"] = self.readString()
        fields["FacebookID"] = self.readString()
        fields["GamecenterID"] = self.readString()
        fields["ServerMajorVersion"] = self.readInt()
        fields["ContentVersion"] = self.readInt()
        fields["ServerBuild"] = self.readInt()
        fields["ServerEnvironment"] = self.readString()
        fields["SessionCount"] = self.readInt()
        fields["PlayTimeSeconds"] = self.readInt()
        fields["DaysSinceStartedPlaying"] = self.readInt()
        fields["FacebookAppID"] = self.readString()
        fields["ServerTime"] = self.readString()
        fields["AccountCreatedDate"] = self.readString()
        fields["StartupCooldownSeconds"] = self.readInt()
        fields["GoogleServiceID"] = self.readString()
        fields["LoginCountry"] = self.readString()
        fields["KunlunID"] = self.readString()
        fields["Tier"] = self.readInt()
        fields["TencentID"] = self.readString()
       
        ContentUrlCount = self.readInt()
        fields["GameAssetsUrls"] = []
        for i in range(ContentUrlCount):
            fields["GameAssetsUrls"].append(self.readString())
       
        EventUrlCount = self.readInt()
        fields["EventAssetsUrls"] = []
        for i in range(EventUrlCount):
            fields["EventAssetsUrls"].append(self.readString())
       
        fields["SecondsUntilAccountDeletion"] = self.readVInt()
        fields["SupercellIDToken"] = self.readCompressedString()
        fields["IsSupercellIDLogoutAllDevicesAllowed"] = self.readBoolean()
        fields["isSupercellIDEligible"] = self.readBoolean()
        fields["LineID"] = self.readString()
        fields["SessionID"] = self.readString()
        fields["KakaoID"] = self.readString()
        fields["UpdateURL"] = self.readString()
        fields["YoozooPayNotifyUrl"] = self.readString()
        fields["UnbotifyEnabled"] = self.readBoolean()
        super().decode(fields)
        return fields

    def execute(message, calling_instance, fields):
        pass

    def getMessageType(self):
        return 24101

    def getMessageVersion(self):
        return self.messageVersion