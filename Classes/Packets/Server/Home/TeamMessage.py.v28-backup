from Classes.Packets.PiranhaMessage import PiranhaMessage
from Classes.DB.DynamicDB import DynamicDB
from Classes.TeamManager import (
    get_room,
    get_room_player,
    get_room_players,
)


class TeamMessage(PiranhaMessage):
    def __init__(self, messageData):
        super().__init__(messageData)
        self.id = 24124
        self.messageVersion = 0
        self.roomType = 0

    def _database(self, member, player_id):
        database = getattr(member, "_db_dyn", None) if member is not None else None
        if database is None:
            database = DynamicDB(player_id=str(player_id))
        return database

    def _database_value(self, database, member, method_name, attribute, default=0):
        method = getattr(database, method_name, None)
        if callable(method):
            try:
                return method()
            except Exception:
                pass
        if member is not None:
            value = getattr(member, attribute, None)
            if value is not None:
                return value
        return default

    def _vip_enabled(self, database, member):
        vip_grades = (
            ("get_bronze", "Bronze"),
            ("get_silver", "Silver"),
            ("get_ruby", "Ruby"),
            ("get_rainbow", "Rainbow"),
            ("get_rainbow_x", "RainbowX"),
        )
        for method_name, attribute in vip_grades:
            if bool(self._database_value(database, member, method_name, attribute, False)):
                return True
        return False

    def _member_values(self, room_id, member_data, fallback_player):
        player_id = int(member_data.get("plrID", 0) or 0)
        member = get_room_player(room_id, player_id)
        if member is None and fallback_player is not None:
            if int(getattr(fallback_player, "LowID", 0) or 0) == player_id:
                member = fallback_player

        database = self._database(member, player_id)
        brawler_id = int(self._database_value(
            database, member, "get_selected_brawler", "SelectedBrawler", 0
        ) or 0)

        trophies_method = getattr(database, "get_brawler_trophies", None)
        if callable(trophies_method):
            try:
                trophies = int(trophies_method(brawler_id))
            except Exception:
                trophies = int(getattr(member, "BrawlerTrophies", 0) or 0)
        else:
            trophies = int(getattr(member, "BrawlerTrophies", 0) or 0)

        selected_skins = getattr(member, "SelectedSkins", {}) if member is not None else {}
        skin_id = selected_skins.get(brawler_id, selected_skins.get(str(brawler_id), 0))

        power_level = getattr(member, "TeamBPL", None) if member is not None else None
        if power_level is None and member is not None:
            power_level = getattr(member, "BrawlerLevel", 0)

        name = self._database_value(database, member, "get_name", "Name", "")
        name_color = int(self._database_value(
            database, member, "get_name_color", "Namecolor", 0
        ) or 0)
        thumbnail = int(getattr(member, "Thumbnail", 0) or 0) if member is not None else 0

        return {
            "player_id": player_id,
            "member": member,
            "brawler_id": brawler_id,
            "skin_id": int(skin_id or 0),
            "trophies": trophies,
            "power_level": int(power_level or 0),
            "name": str(name or member_data.get("NAME", "")),
            "name_color": name_color,
            "thumbnail": thumbnail,
            "is_vip": self._vip_enabled(database, member),
        }

    def encode(self, fields, player):
        team_id = getattr(player, "TeamID", [0, 0])
        room_id = int(team_id[1] or 0) if team_id and len(team_id) > 1 else 0
        room = get_room(room_id)

        if room is None:
            player_id = int(getattr(player, "LowID", 0) or 0)
            room = {
                "id": room_id,
                "mapID": int(getattr(player, "SelectedMap", 1) or 1),
                "roomType": self.roomType,
                "Tick": 1,
                "premade": [],
                "msg": [],
                "invites": [],
                "players": [{
                    "plrID": player_id,
                    "STAT": 2,
                    "READY": bool(getattr(player, "isReady", False)),
                    "NAME": str(getattr(player, "Name", "")),
                    "OWNER": True,
                }],
            }

        # Sync readiness once, then encode a detached room snapshot. A team
        # change arriving during serialization must not alter row counts or
        # member order halfway through this packet.
        get_room_players(room_id)
        players = [dict(member_data) for member_data in room.get("players", [])]
        if not players:
            players = [{
                "plrID": int(getattr(player, "LowID", 0) or 0),
                "STAT": 2,
                "READY": bool(getattr(player, "isReady", False)),
                "NAME": str(getattr(player, "Name", "")),
                "OWNER": True,
            }]

        # Normalize per-player state before every snapshot so no member can
        # retain a stale ClubWar flag between TeamMessage broadcasts.
        if "ClubWar" in room:
            room["ClubWar"] = False
        if hasattr(player, "ClubWar"):
            player.ClubWar = False
        for member_data in players:
            member = get_room_player(room.get("id", room_id), member_data.get("plrID"))
            if member is not None and hasattr(member, "ClubWar"):
                member.ClubWar = False

        room_type = int(room.get("roomType", self.roomType) or 0)
        map_id = int(room.get("mapID", getattr(player, "SelectedMap", 1)) or 0)
        room_low_id = int(room.get("id", room_id) or 0)

        # Header and player field order match Server/Team/TeamMessage.py in v28.
        self.writeVInt(room_type)
        self.writeBoolean(False)  # Club War is disabled for every team.
        self.writeVInt(1)

        self.writeInt(0)
        self.writeInt(room_low_id)

        self.writeVInt(1557129593)
        self.writeVInt(0)
        self.writeVInt(0)
        self.writeVInt(0)

        self.writeVLong(15, map_id)

        player_count = len(players)
        for member_data in players:
            values = self._member_values(room_low_id, member_data, player)

            # Keep the v28 repetition of player count for each member entry.
            self.writeVInt(player_count)
            self.writeVInt(1 if member_data.get("OWNER", False) else 0)
            self.writeInt(0)
            self.writeInt(values["player_id"])

            self.writeVLong(16, values["brawler_id"])
            self.writeVLong(29, values["skin_id"])
            self.writeVInt(values["trophies"])
            self.writeVInt(values["trophies"])
            self.writeVInt(values["power_level"])
            self.writeVInt(int(member_data.get("STAT", 2) or 0))
            self.writeVInt(1 if member_data.get("READY", False) else 0)
            self.writeVInt(0)
            self.writeVInt(0)
            self.writeVInt(0)

            self.writeString(values["name"])
            self.writeVInt(100)
            self.writeVInt(28000000 + values["thumbnail"])
            self.writeVInt(43000000 + values["name_color"])
            self.writeVInt(43000000 + values["name_color"] if values["is_vip"] else 0)

            # v28's TeamMessage writes two zero slots here.
            self.writeVInt(0)
            self.writeVInt(0)

        # The count must describe exactly the invites written below.
        invites = [
            dict(invite)
            for invite in room.get("invites", [])
            if invite.get("state", 0) == 0
        ]
        self.writeVInt(len(invites))
        for invite in invites:
            invite_id = int(invite.get("id", 0) or 0)
            invite_database = DynamicDB(player_id=str(invite_id))
            invite_name = invite_database.get_name()

            self.writeVInt(1)
            self.writeVInt(1)
            self.writeInt(0)
            self.writeInt(room_low_id)
            self.writeInt(0)
            self.writeInt(invite_id)
            self.writeString(invite_name)
            self.writeVInt(1)
            self.writeVInt(len(invites))

        self.writeVInt(0)
        self.writeVInt(0)
        self.writeVInt(2)

    def decode(self):
        fields = {}
        fields["PlayerCount"] = self.readVInt()
        fields["Text"] = self.readString()
        fields["Unk1"] = self.readVInt()
        super().decode(fields)
        return {}

    def execute(message, calling_instance, fields):
        pass

    def getMessageType(self):
        return 24124

    def getMessageVersion(self):
        return self.messageVersion
