from Classes.DB.AllianceDB import AllianceDatabase
from Classes.DB.DynamicDB import DynamicDB as DB
from Classes.Packets.PiranhaMessage import PiranhaMessage


class MyAllianceMessage(PiranhaMessage):

    def __init__(self, messageData):
        super().__init__(messageData)
        self.messageVersion = 0
        self.id = 24399

    def decode(self):
        pass  # Non serve decode, è server→client

    def encode(self, fields, player):
        if fields is None:
            fields = {}
        fields["Socket"] = player.client

        # Usa player.ClubLowID (il club del player), non self.clubLowID
        if player.ClubLowID != 0:
            club_data = player.alliance_db.getAlliance(player.ClubLowID)
            
            if club_data is None:
                print(f"[MyAllianceMessage] ERROR: Club {player.ClubLowID} not found for player {player.LowID}")
                self.writeVInt(0)
                self.writeVInt(0)
                return
            
            # === CALCOLA I TROFEI TOTALI REALI DEL CLUB DAL DB DEI MEMBRI ===
            members = player.alliance_db.getMembers(player.ClubLowID)
            real_club_trophies = 0
            
            for member in members:
                member_low_id = member["player_id"]
                try:
                    member_db = DB(player_id=str(member_low_id))
                    member_trophies = member_db.get_total_trophies()
                    real_club_trophies += member_trophies
                    print(f"[MyAlliance] Member {member['name']} (ID: {member_low_id}): {member_trophies} trophies")
                except Exception as e:
                    print(f"[MyAlliance] Error getting trophies for member {member_low_id}: {e}")
                    # Fallback: usa i trofei salvati nell'alliance DB
                    real_club_trophies += member.get("trophies", 0)
            
            print(f"[MyAlliance] Club {club_data['name']} - Real Total Trophies: {real_club_trophies}")
            
            self.writeVInt(club_data["member_count"] - 1)
            self.writeVInt(1)
            self.writeVInt(25)
            self.writeVInt(player.ClubRole)

            self.writeInt(0)
            self.writeInt(player.ClubLowID)
            self.writeString(club_data["name"])

            self.writeVInt(8)
            self.writeVInt(club_data["badge_id"])

            self.writeVInt(club_data["type"])
            self.writeVInt(club_data["member_count"] - 1)

            self.writeVInt(real_club_trophies)  # Usa i trofei reali calcolati dal DB
            self.writeVInt(club_data["trophies_needed"])

            self.writeVInt(0)
            self.writeString(club_data["region"])
            
            self.writeVInt(0)
            self.writeVInt(club_data["friendly_family"])

        else:
            print(f"[MyAllianceMessage] Player {player.LowID} not in any club")
            self.writeVInt(0)
            self.writeVInt(0)

    def getMessageType(self):
        return self.id

    def getMessageVersion(self):
        return self.messageVersion