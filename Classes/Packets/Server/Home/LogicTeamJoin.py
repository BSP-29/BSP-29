from Classes.Commands.LogicCommand import LogicCommand
from Classes.Messaging import Messaging
from Classes.TeamManager import add_member, get_room_players, get_team


class LogicJoinTeamCommand(LogicCommand):
    def __init__(self, commandData):
        super().__init__(commandData)

    def encode(self, fields):
        LogicCommand.encode(self, fields)
        self.writeVInt(0)
        return self.messagePayload

    def decode(self, calling_instance):
        fields = {}
        LogicCommand.decode(calling_instance, fields, False)
        fields["TeamID"] = calling_instance.readVInt()
        LogicCommand.parseFields(fields)
        return fields

    def execute(self, calling_instance, fields, cryptoInit):
        team_id = fields["TeamID"]
        player = calling_instance.player

        if not add_member(team_id, player):
            return

        team = get_team(team_id)
        if team is None:
            return

        for member in get_room_players(team_id):
            session = getattr(member, "session", None)
            if session is None or not hasattr(session, "client") or not hasattr(session, "cryptoInit"):
                continue
            Messaging.sendMessage(
                24124,
                {"Socket": session.client},
                session.cryptoInit,
                member
            )

    def getCommandType(self):
        return 530