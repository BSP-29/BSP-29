from Classes.Commands.LogicCommand import LogicCommand
from Classes.Messaging import Messaging
from Classes.DB.DynamicDB import DynamicDB
from Classes.Instances.Classes.Player import Player

class LogicPurchaseOfferCommand(LogicCommand):
    def __init__(self, commandData):
        super().__init__(commandData)

    def execute(self, calling_instance, fields, cryptoInit):
        player = calling_instance.player
        offer_id = int(fields["OfferID"])

        # --- GESTIONE COLORI (0-16) ---
        if 0 <= offer_id <= 16:
            db = DynamicDB(player_id=str(player.LowID)) 
            db.set_name_color(offer_id) 
            player.Namecolor = offer_id
            Messaging.sendMessage(24104, {
                "Socket": calling_instance.client, 
                "Tick": 0, 
                "ServerChecksum": 0, 
                "ClientChecksum": 0
            }, cryptoInit, player)
            return

    def decode(self, calling_instance):
        fields = {}
        LogicCommand.decode(calling_instance, fields, False)
        fields["OfferID"] = calling_instance.readVInt()
        fields["Unk2"] = calling_instance.readDataReference()
        return fields

    def getCommandType(self):
        return 519