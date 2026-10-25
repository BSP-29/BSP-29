"""203, LogicGiveDeliveryItems, the reward box the client opens.

Always a Mega Box (ID 10) with random resource loot: coins, gems, token
doublers, generic power points. No brawlers, skins or star powers.
"""
from Classes.Commands.LogicServerCommand import LogicServerCommand
from Classes.Commands.LogicCommand import LogicCommand
from Classes.Logic.RewardDelivery import (
    BOX_MEGA,
    REWARD_COINS,
    REWARD_GEMS,
    TRACK_BRAWL_PASS,
    build_delivery,
    grant,
    random_resource_rewards,
)

import random


class LogicGiveDeliveryItemsCommand(LogicServerCommand):

    def __init__(self, commandData, player=None):
        super().__init__(commandData)
        self.player = player

    def decode(self, calling_instance):
        # The reference LogicGiveDeliveryItemsCommand has no Decode override,
        # so it inherits Command.Decode, which reads only the four header
        # VInts. Reading more here eats into the next command in the same
        # EndClientTurn and misaligns the stream, which is what produced the
        # malformed packets and the empty responses.
        fields = {}
        LogicCommand.decode(calling_instance, fields, False)
        LogicCommand.parseFields(fields)
        return fields

    def encode(self, fields):
        box_id = 100  # Royale's most common box type
        track = int(fields.get("TrackType", TRACK_BRAWL_PASS) or TRACK_BRAWL_PASS)
        rank = int(fields.get("RewardRank", 0) or 0)
        rewards = random_resource_rewards()

        self.messagePayload += bytes(build_delivery(rewards, box_id, track, rank))
        return self.messagePayload

    def execute(self, calling_instance, fields, cryptoInit):
        player = getattr(calling_instance, "player", None)
        print(f"[203] execute called, account={getattr(player, 'LowID', '?')}, fields={fields}")
        # The client sends 203 when the user clicks "open box". Do not
        # generate new rewards here.

    def getCommandType(self):
        return 203