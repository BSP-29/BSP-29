from Classes.DB.DynamicDB import DynamicDB
from Classes.Packets.PiranhaMessage import PiranhaMessage
from Classes.Messaging import Messaging
import threading
import time

class SetInvitesBlockedMessage(PiranhaMessage):
    def __init__(self, messageData):
        super().__init__(messageData)
        self.messageVersion = 0

    def decode(self):
        fields = {}
        super().decode(fields)
        return fields

    def encode(self, fields, player):
        return

    def execute(self, calling_instance, fields, cryptoInit):
        player = calling_instance.player
        dyn = DynamicDB(player_id=str(player.LowID))

        current = dyn.get_dnd_state()
        new_value = 0 if current == 1 else 1

        dyn.set_dnd_state(new_value)
        player.DnDState = new_value

        print(f">>> DnD toggled {current} -> {new_value}. Sending DnDOK (20174)")

        Messaging.sendMessage(20174, fields, cryptoInit, player)

    def delayed_close():
        pass
                              
    def getMessageType(self):
        return 14777

    def getMessageVersion(self):
        return self.messageVersion