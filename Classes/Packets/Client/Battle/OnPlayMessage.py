from Classes.Packets.PiranhaMessage import PiranhaMessage


class OnPlayMessage(PiranhaMessage):
    """Start an immediate practice battle for a solo lobby player."""

    def __init__(self, messageData):
        super().__init__(messageData)
        self.messageVersion = 0

    def encode(self, fields):
        pass

    def decode(self):
        fields = {}
        # v29 sends: unknown, card ID, unknown, and event/map slot.
        values = ("Unknown1", "CardID", "Unknown2", "MapIndex")
        for name in values:
            if self.offset >= self.length:
                break
            fields[name] = self.readVInt()
        super().decode(fields)
        return fields

    def execute(message, calling_instance, fields, cryptoInit):
        player = calling_instance.player
        map_index = int(fields.get("MapIndex", 0) or 0)
        room_id = 0
        team_id = getattr(player, "TeamID", [0, 0])
        if team_id and len(team_id) > 1:
            room_id = int(team_id[1] or 0)

        if room_id:
            from Classes.TeamManager import set_room_map
            from Classes.TeamMatchmaking import all_members_ready, start_matchmaking
            # The last vint of 14103 is the location the client wants. Apply it
            # to the room before starting so the battle, the loading screen and
            # the team lobby all use the map the player actually chose.
            if map_index > 0:
                set_room_map(room_id, map_index)
                player.SelectedMap = map_index
            if all_members_ready(room_id):
                start_matchmaking(room_id)
            return

        # OnPlay's map slot is the location id used by the v29 start-loading
        # packet. This bypasses an empty search queue and starts with bots.
        from Classes.BattleServer import start_solo_battle
        selected_map = map_index
        if selected_map <= 0:
            try:
                selected_map = int(getattr(player, "SelectedMap", 0) or 0)
            except (TypeError, ValueError):
                selected_map = 0
        if not start_solo_battle(player, selected_map):
            print(f"[Battle] Immediate start failed for location {selected_map}")

    def getMessageType(self):
        return 14103

    def getMessageVersion(self):
        return self.messageVersion
