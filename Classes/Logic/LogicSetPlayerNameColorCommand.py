from Classes.Packets.PiranhaMessage import PiranhaMessage
from Classes.DB.DynamicDB import DynamicDB 
from Classes.Commands.LogicServerCommand import LogicServerCommand
from Classes.Messaging import Messaging

class LogicSetPlayerNameColorCommand(LogicServerCommand):
    def __init__(self, commandData):
        super().__init__(commandData)

    def decode(self, calling_instance):
        fields = {}
        for i in range(5):
            calling_instance.readVInt()
        fields["NameColor"] = calling_instance.readVInt()
        self.fields = fields
        return fields

    def execute(self, calling_instance, fields, cryptoInit):
        player = calling_instance.player
        requested_color = fields["NameColor"]
        
        # --- DEBUG CONSOLE ---
        print(f"--- [DEBUG COLOR CHECK] ---")
        print(f"Giocatore: {player.Name}")
        print(f"Colore Richiesto: {requested_color} (Tipo: {type(requested_color)})")
        
        # === LEGGI DIRETTAMENTE DAL DB (più sicuro) ===
        db = DynamicDB(player_id=str(player.LowID))
        is_bronze = db.get_bronze()
        is_silver = db.get_silver()
        is_ruby = db.get_ruby()
        is_rainbow = db.get_rainbow()
        is_rainbowx = db.get_rainbow_x()
        
        print(f"Bronze: {is_bronze} (Tipo: {type(is_bronze)})")
        print(f"Silver: {is_silver} (Tipo: {type(is_silver)})")
        print(f"Ruby: {is_ruby} (Tipo: {type(is_ruby)})")
        print(f"Rainbow: {is_rainbow} (Tipo: {type(is_rainbow)})")
        print(f"RainbowX: {is_rainbowx} (Tipo: {type(is_rainbowx)})")

        # Mappa dei colori sbloccabili
        color_requirements = {
            12: is_bronze,
            13: is_silver,
            14: is_ruby,
            15: is_rainbow,
            16: is_rainbowx
        }

        # Colori base sempre disponibili (0-11)
        if requested_color <= 11:
            # Tutti i colori base sono disponibili
            pass
        elif requested_color in color_requirements and not color_requirements[requested_color]:
            print(f"🚫 BLOCCO: {player.Name} non ha il grado per il colore {requested_color}")
            print(f"   Debug: bronze={is_bronze}, silver={is_silver}, ruby={is_ruby}, rainbow={is_rainbow}, rainbowx={is_rainbowx}")
            Messaging.sendMessage(24104, {
                "Socket": calling_instance.client, 
                "Tick": 0, 
                "ServerChecksum": 0, 
                "ClientChecksum": 0
            }, cryptoInit, player)
            return
        elif requested_color > 16:
            print(f"🚫 BLOCCO: Colore {requested_color} non valido")
            Messaging.sendMessage(24104, {
                "Socket": calling_instance.client, 
                "Tick": 0, 
                "ServerChecksum": 0, 
                "ClientChecksum": 0
            }, cryptoInit, player)
            return

        # --- SALVATAGGIO ---
        db.set_name_color(requested_color) 
        player.Namecolor = requested_color
        player.load_from_db()  # Ricarica per sincronizzare
        
        print(f"✅ SALVATO: Colore {requested_color} per {player.Name}")

    def getCommandType(self):
        return 527