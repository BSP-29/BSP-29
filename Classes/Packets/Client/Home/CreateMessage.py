from time import daylight
from random import choice
from string import ascii_uppercase
import json
from Classes.Messaging import Messaging
from Classes.Packets.PiranhaMessage import PiranhaMessage


class CreateMessage(PiranhaMessage):
    def __init__(self, messageData):
        super().__init__(messageData)
        self.id = 14301
        self.messageVersion = 0

    def decode(self):
        # ClubID
        self.clubHighID = 0

        # Info
        self.clubName           = self.readString()    # Club name 
        self.clubdescription    = self.readString()    # Club description

        # Badge
        self.BadgeIdentifier    = self.readVInt()      # Badge Identifier
        self.clubbadgeID        = self.readVInt()      # BadgeID

        # Region
        self.RegionIdentifier   = self.readVInt()      # Region Identifier
        self.clubregionID       = self.readVInt()      # RegionID 

        # Settings
        self.clubtype           = self.readVInt()      # Type
        self.clubtrophiesneeded = self.readVInt()      # Trophy required
        self.clubfriendlyfamily = self.readVInt()      # Family friendly

    def execute(self, calling_instance, fields, cryptoInit):
        # Inizializza fields se è None
        if fields is None:
            fields = {}

        fields["Socket"] = calling_instance.client
        player = calling_instance.player

        # Imposta i dati club sul player
        player.ClubName = self.clubName
        player.ClubDescription = self.clubdescription
        player.ClubIcon = self.clubbadgeID
        player.ClubType = self.clubtype
        player.ClubTrophiesNeed = self.clubtrophiesneeded
        player.ClubMinimumJoinTrophies = self.clubtrophiesneeded
        player.ClubFamilyFriendly = (self.clubfriendlyfamily == 1)
        player.FamilyFriendly = player.ClubFamilyFriendly
        player.ClubMemberCount = 1
        player.ClubRole = 2           # 2 = President
        player.IsInAlliance = True

        # Crea l'alliance nel DB usando l'istanza AllianceDatabase del player
        alliance_id = player.alliance_db.createAlliance(player)

        if alliance_id is not None:
            player.ClubLowID = alliance_id
            print(f"[CreateMessage] Alliance created with ID: {alliance_id}")
        else:
            print(f"[CreateMessage] ERROR: Failed to create alliance for player {player.LowID}")

        # Ricarica i dati dal DB dentro il player (ClubName, MemberCount, ecc.)
        player.load_alliance()

        # Messaggi verso il client
        Messaging.sendMessage(24333, fields, cryptoInit, player, calling_instance)
        Messaging.sendMessage(24399, fields, cryptoInit, player, calling_instance)
        # AllianceStreamMessage(self.client, self.player, player.ClubLowID, 0).send()

    def getMessageType(self):
        return self.id

    def getMessageVersion(self):
        return self.messageVersion