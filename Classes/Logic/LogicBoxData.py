import random

class LogicBoxData:
    def randomize(self, box_type):
        # Inizializza il dizionario dei premi
        self.box_rewards = {'Rewards': []}
        player = self.player 

        # --- CASSA BRAWL (Type 10) ---
        if box_type == 10:
            # 1. Oro: Aggiorna Coins e la lista resources
            gold = random.randint(20, 100)
            self.box_rewards['Rewards'].append({'Amount': gold, 'DataRef': [0, 0], 'Value': 7})
            player.Coins += gold

            # 2. Punti Energia: Usa gli ID brawler sbloccati
            # Estraiamo gli ID dalle chiavi del dizionario OwnedBrawlers del tuo Player
            unlocked_ids = list(player.OwnedBrawlers.keys())
            if unlocked_ids:
                brawler_id = random.choice(unlocked_ids)
                pp_amount = random.randint(5, 25)
                self.box_rewards['Rewards'].append({'Amount': pp_amount, 'DataRef': [16, brawler_id], 'Value': 6})
                
                # Aggiorna PowerPoints direttamente nel dizionario OwnedBrawlers
                player.OwnedBrawlers[brawler_id]["PowerPoints"] += pp_amount

            # 3. Bonus Gemme (10% chance)
            if random.randint(0, 100) < 10:
                gems = random.randint(3, 10)
                self.box_rewards['Rewards'].append({'Amount': gems, 'DataRef': [0, 0], 'Value': 8})
                player.Gems += gems

        # --- CASSA ENORME (Type 11) ---
        elif box_type == 11:
            # 1. Oro
            gold = random.randint(100, 300)
            self.box_rewards['Rewards'].append({'Amount': gold, 'DataRef': [0, 0], 'Value': 7})
            player.Coins += gold

            # 2. Punti Energia (3 slot per brawler diversi)
            unlocked_ids = list(player.OwnedBrawlers.keys())
            if unlocked_ids:
                sample_size = min(len(unlocked_ids), 3)
                chosen_brawlers = random.sample(unlocked_ids, sample_size)
                for b_id in chosen_brawlers:
                    pp_amount = random.randint(20, 60)
                    self.box_rewards['Rewards'].append({'Amount': pp_amount, 'DataRef': [16, b_id], 'Value': 6})
                    player.OwnedBrawlers[b_id]["PowerPoints"] += pp_amount

        # --- MEGA CASSA (Type 12) ---
        elif box_type == 12:
            # 1. Oro
            gold = random.randint(400, 1000)
            self.box_rewards['Rewards'].append({'Amount': gold, 'DataRef': [0, 0], 'Value': 7})
            player.Coins += gold

            # 2. Punti Energia (5 slot per brawler diversi)
            unlocked_ids = list(player.OwnedBrawlers.keys())
            if unlocked_ids:
                sample_size = min(len(unlocked_ids), 5)
                chosen_brawlers = random.sample(unlocked_ids, sample_size)
                for b_id in chosen_brawlers:
                    pp_amount = random.randint(40, 120)
                    self.box_rewards['Rewards'].append({'Amount': pp_amount, 'DataRef': [16, b_id], 'Value': 6})
                    player.OwnedBrawlers[b_id]["PowerPoints"] += pp_amount

            # 3. Bonus Raddoppia Gettoni (Sempre nelle Mega)
            doubler = random.randint(200, 400)
            self.box_rewards['Rewards'].append({'Amount': doubler, 'DataRef': [0, 0], 'Value': 2})
            player.TokensDoubler += doubler

        return self.box_rewards