from Classes.Logic.BrawlerLoadout import resolve_power_level
from Classes.Packets.PiranhaMessage import PiranhaMessage

class BattleEndMessage(PiranhaMessage):
    def __init__(self, messageData):
        super().__init__(messageData)
        self.messageVersion = 0

    def encode(self, fields, player):
        original_gm = fields["GameMode"]  # GameMode originale per calcolo trofei
        gm_type = BattleEndMessage.getGameModeType(original_gm)  # GameMode convertito per il client
        result = fields["Unk1"]
        
        selected_brawler = player.SelectedBrawler
        
        # === OTTIENI I TROFEI CORRENTI DIRETTAMENTE DAL DB ===
        current_trophies = player._db_dyn.get_brawler_trophies(selected_brawler)
        
        print(f"[BattleEnd] Brawler {selected_brawler} - Current trophies from DB: {current_trophies}")

        # === CALCOLA TROFEI (usa original_gm) ===
        trophies_reward = 0

        if original_gm == 1 or original_gm not in [6, 9]:  # 3v3 o GameMode non riconosciuto
            if result == 0:
                trophies_reward = 10
                player.Wins += 1
            elif result == 1:
                trophies_reward = -10

        elif original_gm == 6:  # Solo Showdown
            solo_rewards = {
                1: 25, 2: 20, 3: 15, 4: 10, 5: 5,
                6: -5, 7: -10, 8: -15, 9: -20, 10: -25
            }
            trophies_reward = solo_rewards.get(result, 0)
            if result == 1:
                player.Wins += 1

        elif original_gm == 9:  # Duo Showdown
            duo_rewards = {1: 20, 2: 10, 3: -5, 4: -15, 5: -25}
            trophies_reward = duo_rewards.get(result, 0)
            if result == 1:
                player.Wins += 1

        new_trophies = max(0, current_trophies + trophies_reward)
        
        # === SALVA NEL DB ===
        try:
            player._db_dyn.set_brawler_trophies(selected_brawler, new_trophies)
            print(f"[BattleEnd] ✅ Saved to DB: brawler {selected_brawler} = {new_trophies}")
        except Exception as e:
            print(f"[BattleEnd] ❌ ERROR saving to DB: {e}")
            new_trophies = current_trophies
        
        # === IMPOSTA TrophiesRewarded PER L'ANIMAZIONE ===
        player.TrophiesRewarded = trophies_reward

        # === BATTLEQUESTTYPE ===
        if gm_type == 2:
            player.BattleQuestType = 1 if 1 <= result <= 4 else 0
        elif gm_type == 5:
            player.BattleQuestType = 1 if result in (1, 2) else 0
        else:
            player.BattleQuestType = 1 if result == 0 else 0

        print(f"[BattleEnd] Original GM:{original_gm} | Client GM:{gm_type} | Result:{result} | Trophies:{trophies_reward} | Brawler:{selected_brawler} | New:{new_trophies}")

        # === SEZIONE 1: VINT INIZIALI (usa gm_type per il client) ===
        self.writeVInt(gm_type)
        self.writeVInt(result)
        self.writeVInt(2000)
        self.writeVInt(trophies_reward)
        self.writeVInt(0)
        self.writeVInt(0)
        self.writeVInt(0)
        self.writeVInt(0)
        self.writeVInt(0)
        self.writeVInt(0)
        self.writeVInt(0)
        self.writeVInt(0)
        self.writeVInt(0)
        self.writeVInt(0)
        self.writeVInt(0)
        self.writeVInt(0)
        self.writeVInt(0)

        # === SEZIONE 2: BOOLEAN ===
        self.writeBoolean(False)
        self.writeBoolean(False)
        self.writeBoolean(False)
        self.writeBoolean(False)
        self.writeBoolean(True)
        self.writeBoolean(False)
        self.writeBoolean(False)

        # === SEZIONE 3: BATTLE TYPE ===
        self.writeVInt(-1)
        self.writeBoolean(False)

        # === SEZIONE 4: PLAYER ARRAY ===
        self.writeVInt(fields["HeroesCount"])
        for heroEntry in fields["Heroes"]:
            is_own_player = heroEntry["IsPlayer"]
            brawler_id = heroEntry["Brawler"]["ID"][1]
            
            # Ottieni i trofei dal DB per ogni brawler
            brawler_trophies = player._db_dyn.get_brawler_trophies(brawler_id)
            
            self.writeBoolean(is_own_player) 
            self.writeBoolean(heroEntry["Team"] != fields["Heroes"][0]["Team"]) 
            self.writeBoolean(is_own_player)
            
            self.writeDataReference(heroEntry["Brawler"]["ID"][0], heroEntry["Brawler"]["ID"][1])
            self.writeDataReference(heroEntry["Brawler"]["SkinID"][0], heroEntry["Brawler"]["SkinID"][1])
            
            self.writeVInt(brawler_trophies)
            self.writeVInt(0)
            self.writeVInt(resolve_power_level(player, brawler_id))
            
            self.writeBoolean(is_own_player)
            if is_own_player:
                self.writeLong(player.ID[0], player.LowID)
            
            self.writeString(heroEntry["PlayerName"])
            self.writeVInt(100)
            self.writeVInt(28000000 + player.Thumbnail)
            self.writeVInt(43000000 + player.Namecolor)
            self.writeVInt(4600001)

        # === SEZIONE 5: EXPERIENCE REWARDS ===
        self.writeVInt(2)
        self.writeVInt(0)
        self.writeVInt(67)
        self.writeVInt(8)
        self.writeVInt(104)

        # === SEZIONE 6: MILESTONE REWARDS ===
        self.writeVInt(0)

        # === SEZIONE 7: PLAYER STATS ===
        # Usa (new_trophies - trophies_reward) per evitare visual glitches
        display_trophies = new_trophies - trophies_reward
        self.writeVInt(2)
        self.writeVInt(1)
        self.writeVInt(display_trophies)  # Trofei prima della partita
        self.writeVInt(display_trophies)  # Trofei prima della partita
        self.writeVInt(5)
        self.writeVInt(player.Experience)
        self.writeVInt(player.Experience)

        # === SEZIONE 8: DATA REFERENCE ===
        self.writeDataReference(28, 0)
        self.writeBoolean(False)

        # === SEZIONE 9: PROGRESSIVE QUESTS ===
        self.writeBoolean(True)
        self.writeVInt(1)

        self.writeVInt(player.BattleQuestWin) 
        self.writeVInt(2) 
        self.writeVInt(player.BattleQuestType)
        self.writeVInt(9)  
        self.writeVInt(10) 
        self.writeVInt(2000) 
        self.writeVInt(player.BattleQuestWin)
        self.writeVInt(player.BattleQuestWin) 
        self.writeVInt(player.BattleQuestWin) 
        self.writeVInt(1) 
        self.writeBoolean(False) 
        self.writeBoolean(True)  
        self.writeDataReference(16, selected_brawler) 
        self.writeVInt(0) 
        self.writeVInt(player.BattleQuestWin)
        self.writeVInt(player.BattleQuestWin)

    def decode(self):
        return {}

    def execute(message, calling_instance, fields):
        pass

    def getMessageType(self):
        return 23456

    def getMessageVersion(self):
        return self.messageVersion
    
    @staticmethod
    def getGameModeType(gm_type):
        if gm_type in [6, 14, 15]:
            return 2
        elif gm_type == 8:
            return 3
        elif gm_type == 7:
            return 4
        elif gm_type == 9:
            return 5
        elif gm_type in [10, 18]:
            return 6
        else:
            return 1