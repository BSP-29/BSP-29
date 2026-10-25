import json
import os
from Classes.Messaging import Messaging
from Classes.Packets.PiranhaMessage import PiranhaMessage

class SendAllianceInvitationMessage(PiranhaMessage):
    def __init__(self, messageData):
        super().__init__(messageData)
        self.messageVersion = 0

    def decode(self):
        fields = {}
        fields["HighID"] = self.readInt()
        fields["LowID"] = self.readInt() # ID della persona da invitare/aggiungere
        super().decode(fields)
        return fields

    def execute(self, calling_instance, fields, cryptoInit):
        player = calling_instance.player
        target_low_id = fields["LowID"]

        # --- 1. AGGIORNA IL PLAYER ATTUALE (Mittente) ---
        sender_friends = player._db_dyn.get_friends_list()
        
        # Verifica se esiste già una relazione con questo ID
        if not any(f['id'] == target_low_id for f in sender_friends):
            # Stato 3: Richiesta Inviata
            sender_friends.append({'id': target_low_id, 'state': 3})
            player._db_dyn.set_friends_list(sender_friends)

        # --- 2. AGGIORNA IL DESTINATARIO (Ricevente) ---
        target_path = f"data/dynamic/0-{target_low_id}.json"
        if os.path.exists(target_path):
            with open(target_path, 'r') as f:
                target_data = json.load(f)
            
            target_friends = target_data.get("Friends", [])
            
            # Verifica se il destinatario ha già la richiesta
            if not any(f['id'] == player.LowID for f in target_friends):
                # Stato 2: Richiesta Ricevuta
                target_friends.append({'id': player.LowID, 'state': 2})
                target_data["Friends"] = target_friends
                
                with open(target_path, 'w') as f:
                    json.dump(target_data, f, indent=4)
            
            print(f"📩 Invito social inviato da {player.LowID} a {target_low_id}")
        else:
            print(f"⚠️ Giocatore {target_low_id} non trovato nel DB.")

        # --- 3. AGGIORNA LA LISTA ---
        Messaging.sendMessage(20105, {
            "Socket": calling_instance.client
        }, cryptoInit, player)

    def getMessageVersion(self):
        return self.messageVersion

    def getMessageType(self):
        return 14316