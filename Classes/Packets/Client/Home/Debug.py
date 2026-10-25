import struct
from Classes.Packets.PiranhaMessage import PiranhaMessage
from Classes.Messaging import Messaging

class DebugCommandMessage(PiranhaMessage):
    def __init__(self, messageData):
        super().__init__(messageData)
        # self.messageBuffer è già impostato da PiranhaMessage.__init__

    def decode(self):
        # Usa self.messageBuffer che contiene i byte grezzi del pacchetto
        data = self.messageBuffer
        
        # Debug opzionale: stampa l'hex per verificare la struttura
        # print(f"[DEBUG] Raw Hex: {data.hex()}")

        if len(data) < 11:
            print(f"[-] Pacchetto Debug troppo corto: {len(data)} bytes")
            return {}

        try:
            # La struttura inviata dallo script JS è:
            # Byte 0-1: Padding/Versione (00 04)
            # Byte 2-3: Message ID (già parsato dal server come 14178)
            # Byte 4-6: Lunghezza/Padding (00 00 00)
            # Byte 7-10: Action ID (Int32 Little Endian)
            
            # Legge l'Action ID dall'offset 7 (Little Endian)
            action_id = struct.unpack_from('<i', data, 7)[0]
        except Exception as e:
            print(f"[-] Errore decoding Action ID: {e}")
            return {}
        
        # Ritorna i campi decodificati
        return {
            'action_id': action_id
        }

    def execute(self, calling_instance, fields, cryptoInit):
        player = calling_instance.player
        action_id = fields.get('action_id')
        
        print(f"[DEBUG] Ricevuta Debug Command ID: {action_id} da Player {player.Name} ({player.LowID})")

        if action_id == 1:
            # Gems +
            added = player._db_dyn.add_gems(100)
            player.Gems = added # Aggiorna anche la RAM
            print(f"[+] Aggiunte 100 Gemme. Totale: {player.Gems}")
            
        elif action_id == 2:
            # Gems -
            added = player._db_dyn.add_gems(-100)
            player.Gems = added
            print(f"[-] Rimosse 100 Gemme. Totale: {player.Gems}")
            
        elif action_id == 3:
            # Coins +
            added = player._db_dyn.add_coins(100)
            player.Coins = added
            print(f"[+] Aggiunti 100 Gettoni. Totale: {player.Coins}")

        # Salva i cambiamenti su disco
        player.update_db()

        # Invia un KeepAlive per confermare
        Messaging.sendMessage(
            20108, # KeepAlive ID (verifica che sia corretto per il tuo server v29)
            {
                "Socket": calling_instance.client,
                "ServerChecksum": 0,
                "ClientChecksum": 0,
                "Tick": 0
            },
            cryptoInit,
            player
        )

    def getMessageType(self):
        return 1536