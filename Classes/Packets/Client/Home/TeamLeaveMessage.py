# Classes/Packets/Client/Home/TeamLeaveMessage.py

from Classes.Packets.PiranhaMessage import PiranhaMessage
from Classes.Packets.Server.Home.TeamLeftMessage import handle_leave_team  


class TeamLeaveMessage(PiranhaMessage):
    def __init__(self, messageData):
        super().__init__(messageData)
        self.messageVersion = 0

    def encode(self, fields):
        # il client non manda payload per il leave
        pass

    def decode(self):
        fields = {}
        super().decode(fields)
        return fields

    def execute(message, calling_instance, fields, cryptoInit):
        print("[TEAM LEAVE DEBUG] TeamLeaveMessage.execute, player:", calling_instance.player.LowID)
        handle_leave_team(calling_instance, cryptoInit)

    def getMessageType(self):
        return 14353  # id client→server di leave, lascia il tuo

    def getMessageVersion(self):
        return self.messageVersion