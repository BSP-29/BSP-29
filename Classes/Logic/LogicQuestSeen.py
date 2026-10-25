from Classes.Commands.LogicCommand import LogicCommand
from Classes.DB.DynamicDB import DynamicDB as DB


class LogicQuestSeenCommand(LogicCommand):
    def __init__(self, commandData):
        super().__init__(commandData)

    def encode(self, fields):
        LogicCommand.encode(self, fields)
        return self.messagePayload

    def decode(self, calling_instance):
        fields = {}
        return fields

    def execute(self, calling_instance, fields, cryptoInit):
        player = calling_instance.player
        db = DB(player_id=str(player.LowID))

        db.set_quest_seen(True)
        print(
            f"[LogicQuestSeenCommand] QuestSeen == True for "
            f"{getattr(player, 'HighID', '?')}-{getattr(player, 'LowID', '?')}"
        )

    def getCommandType(self):
        return 553
