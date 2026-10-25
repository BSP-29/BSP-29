# Classes/Packets/Client/RegionChanger/SetCountryMessage.py
from Classes.DB.DynamicDB import DynamicDB
from Classes.Packets.PiranhaMessage import PiranhaMessage
from Classes.Messaging import Messaging
import threading
import time

class SetCountryMessage(PiranhaMessage):
    def __init__(self, messageData):
        super().__init__(messageData)
        self.raw_data = messageData

    def decode(self):
        return {}

    def execute(self, calling_instance, fields, cryptoInit):
        player = calling_instance.player
        dyn = DynamicDB(player_id=str(player.LowID))
        raw_hex = self.raw_data.hex()
        print(raw_hex)
        
        should_restart = False

        if raw_hex == "0e07":
            dyn.set_theme_id(41000000); dyn.set_region("BSP_1"); player.Region = "BSP_1"
            should_restart = True
        elif raw_hex == "0e08":
            dyn.set_theme_id(41000007); dyn.set_region("BSP_2"); player.Region = "BSP_2"
            should_restart = True
        elif raw_hex == "0e09":
            dyn.set_theme_id(41000001); dyn.set_region("GS"); player.Region = "GS"
            should_restart = True
        elif raw_hex == "0e05":
            dyn.set_theme_id(41000002); dyn.set_region("TS"); player.Region = "TS"
            should_restart = True
        elif raw_hex == "0e0a":
            dyn.set_theme_id(41000003); dyn.set_region("LY"); player.Region = "LY"
            should_restart = True
        elif raw_hex == "0e0b":
            dyn.set_theme_id(41000004); dyn.set_region("WT"); player.Region = "WT"
            should_restart = True
        elif raw_hex == "0e0c":
            dyn.set_theme_id(41000005); dyn.set_region("OG"); player.Region = "OG"
            should_restart = True
        elif raw_hex == "0e0d":
            dyn.set_theme_id(41000006); dyn.set_region("VX"); player.Region = "VX"
            should_restart = True
        elif raw_hex == "0e0e":
            dyn.set_theme_id(41000008); dyn.set_region("VR"); player.Region = "VR"
            should_restart = True
        elif raw_hex == "0e0f":
            dyn.set_theme_id(41000009); dyn.set_region("TP"); player.Region = "TP"
            should_restart = True
        elif raw_hex == "0e10":
            dyn.set_theme_id(41000010); dyn.set_region("SP"); player.Region = "SP"
            should_restart = True

        if should_restart:
            print(f">>> Theme Changed. Sending OutOfSync (24104)")
            
            Messaging.sendMessage(
                24104, 
                {
                    "Socket": calling_instance.client,
                    "ServerChecksum": 0,
                    "ClientChecksum": 0,
                    "Tick": 0
                },
                cryptoInit,
                player 
            )
            
            def delayed_close(socket):
                time.sleep(0.8) 
                try:
                    socket.close()
                    print(">>> Socket chiuso dopo OutOfSync.")
                except:
                    pass

            threading.Thread(target=delayed_close, args=(calling_instance.client,)).start()
        else:
            # Fallback KeepAlive per non bloccare il client se non succede nulla
            Messaging.sendMessage(20108, {"Socket": calling_instance.client, "ServerChecksum": 0, "ClientChecksum": 0, "Tick": 0}, cryptoInit)

    def getMessageType(self):
        return 12998