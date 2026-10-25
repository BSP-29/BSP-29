from Classes.Packets.PiranhaMessage import PiranhaMessage


class AllianceSearchResultMessage(PiranhaMessage):

    def __init__(self, messageData):
        super().__init__(messageData)

        self.messageVersion = 0
        self.id = 24310


    def getMessageVersion(self):
        return self.messageVersion


    def getMessageType(self):
        return self.id


    def encode(self, fields, player):

        searchName = fields["SearchName"]


        alliances = player.alliance_db.getAllAlliances()


        # Resolve every club before writing the count. The old code counted the
        # search hits and then skipped rows whose lookup returned None, so the
        # declared total could exceed the entries actually written.
        clubs = []


        for alliance in alliances:


            if searchName.lower() not in alliance["name"].lower():

                continue


            clubData = player.alliance_db.getAlliance(
                alliance["id"]
            )


            if clubData is None:

                continue


            clubs.append((alliance["id"], clubData))


        self.writeVInt(
            len(clubs)
        )


        for clubLowID, clubData in clubs:


            self.writeInt(0)
            self.writeInt(clubLowID)


            self.writeString(
                clubData["name"]
            )


            self.writeVInt(8)  # AllianceBadge class id
            self.writeVInt(
                clubData["badge_id"]
            )


            self.writeVInt(
                clubData["type"]
            )


            self.writeVInt(
                clubData["member_count"]
            )


            self.writeVInt(
                clubData["trophies"]
            )


            self.writeVInt(
                clubData["trophies_needed"]
            )


            self.writeString(
                clubData["description"]
            )


            self.writeString(
                clubData["region"]
            )


            self.writeBoolean(
                bool(clubData["friendly_family"])
            )