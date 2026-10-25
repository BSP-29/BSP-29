"""536, the Pro token ladder.

Not the claim, that is 517. This is the command the client sends as it earns
tokens, and the amount follows the tier the player's total already puts them
in, using the same threshold table 517 charges against.
"""
from Classes.Commands.LogicCommand import LogicCommand
from Classes.Logic.BrawlPassThresholds import tokens_for_tier_after


class LogicPurchaseBrawlpassProgressCommand(LogicCommand):
    def __init__(self, commandData):
        super().__init__(commandData)

    def encode(self, fields):
        LogicCommand.encode(self, fields)
        return self.messagePayload

    def decode(self, calling_instance):
        fields = {}
        LogicCommand.decode(calling_instance, fields, False)
        LogicCommand.parseFields(fields)
        return fields

    def execute(self, calling_instance, fields, cryptoInit):
        player = calling_instance.player
        database = getattr(player, "_db_dyn", None)
        if database is None:
            return

        before = database.get_brawl_pass_tokens()
        after = tokens_for_tier_after(before, 0)
        database.set_brawl_pass_tokens(after)
        print(f"[Pass] tokens {before} -> {after}")

    def getCommandType(self):
        return 536