from os import SEEK_CUR, curdir
from Classes.DB.AllianceDB import AllianceDatabase
from Classes.DB.DynamicDB import DynamicDB as DB
from Classes.Packets.PiranhaMessage import PiranhaMessage


class AllianceDataMessage(PiranhaMessage):

    def __init__(self, messageData):
        super().__init__(messageData)
        self.id = 24301
        self.messageVersion = 0

    def decode(self):
        # NON leggi nulla - clubLowID viene da fields (passato da AskForAllianceDataMessage)
        pass

    def encode(self, fields, player):
        # === CALCOLA I TROFEI TOTALI REALI DEL CLUB DAL DB DEI MEMBRI ===
        
        # Ottieni clubLowID correttamente
        clubLowID = fields.get("clubLowID", 0) if fields and fields.get("clubLowID", 0) != 0 else getattr(player, 'ClubLowID', getattr(player, 'low_id', 0))
        player_club_low_id = getattr(player, 'ClubLowID', getattr(player, 'low_id', 0))
        
        # Ottieni i membri del club
        members = player.alliance_db.getMembers(clubLowID)
        
        # Calcola trofei totali reali
        real_club_trophies = 0
        
        for member in members:
            member_low_id = member["player_id"]
           
            try:
                member_db = DB(player_id=str(member_low_id))
                member_trophies = member_db.get_total_trophies()
                real_club_trophies += member_trophies
                print(f"[AllianceDataMessage] Member {member['name']} (ID: {member_low_id}): {member_trophies} trophies")
            except Exception as e:
                print(f"[AllianceDataMessage] Error getting trophies for member {member_low_id}: {e}")
                # Fallback: usa i trofei salvati nel club
                real_club_trophies += member.get("trophies", 0)

        # Ottieni i dati del club
        club_data = player.alliance_db.getAlliance(clubLowID)
        
        if club_data:
            print(f"[AllianceDataMessage] Club {club_data['name']} - Real Total Trophies: {real_club_trophies}")
        
        # Scrittura header
        if player_club_low_id != 0:
            self.writeVInt(0)
        else:
            self.writeVInt(2)

        self.writeInt(0)
        self.writeInt(clubLowID)

        # Scrittura dati club
        if club_data is None:
            self.writeString("")
            self.writeVInt(8)
            self.writeVInt(0)
            self.writeVInt(3)
            self.writeVInt(0)
            self.writeVInt(0)
            self.writeVInt(0)
            self.writeVInt(0)
            self.writeVInt(0)
            self.writeString("OG")
            self.writeVInt(0)
            self.writeVInt(0)
            self.writeString("")
            self.writeVInt(0)
            self.writeVInt(0)
        else:
            self.writeString(club_data["name"])
            self.writeVInt(8)
            self.writeVInt(club_data["badge_id"])
            self.writeVInt(club_data["type"])
            self.writeVInt(club_data["member_count"] - 1)
            self.writeVInt(real_club_trophies)  # Usa i trofei reali calcolati
            self.writeVInt(club_data["trophies_needed"])
            self.writeVInt(0)
            self.writeString(club_data["region"])
            self.writeVInt(0)
            self.writeVInt(club_data["friendly_family"])
            self.writeString(club_data.get("description", ""))

        # Scrittura membri
        self.writeVInt(len(members))

        for member in members:
            member_low_id = member["player_id"]
            
            # === OTTIENI I TROFEI REALI DEL MEMBRO DAL DB ===
            try:
                member_db = DB(player_id=str(member_low_id))
                real_trophies = member_db.get_total_trophies()
            except Exception as e:
                print(f"[AllianceData] Error getting trophies for member {member_low_id}: {e}")
                real_trophies = member.get("trophies", 0)
            
            self.writeInt(0)
            self.writeInt(member_low_id)
            self.writeVInt(member["club_role"])
            self.writeVInt(real_trophies)  # Usa i trofei reali dal DB
            self.writeVInt(2)
            self.writeVInt(0)
            self.writeVInt(0)
            self.writeString(member["name"])
            self.writeVInt(member.get("experience", 999999))
            self.writeVInt(28000000 + member.get("thumbnail", 16))
            self.writeVInt(43000000 + member.get("namecolor", 0))
            self.writeVInt(4600001)
            
            print(f"[AllianceData] Member {member['name']} (ID: {member_low_id}): {real_trophies} trophies")

    def getMessageType(self):
        return self.id

    def getMessageVersion(self):
        return self.messageVersion