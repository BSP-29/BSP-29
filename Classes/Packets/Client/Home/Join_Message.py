from Classes.Messaging import Messaging
from Classes.Packets.PiranhaMessage import PiranhaMessage


class JoinMessage(PiranhaMessage):
    def __init__(self, messageData):
        super().__init__(messageData)
        self.id = 14305
        self.messageVersion = 0

    def decode(self):
        # DEBUG: Stampa il buffer PRIMA di leggere
        buffer = self.messageBuffer
        print(f"[JoinMessage] Buffer size: {len(buffer)} bytes")
        print(f"[JoinMessage] Buffer hex: {buffer.hex()}")
        
        # Ora leggi manualmente ogni VInt
        field0 = self.readVInt()
        field1 = self.readVInt()
        field2 = self.readVInt()
        field3 = self.readVInt()
        field4 = self.readVInt()
        field5 = self.readVInt()
        field6 = self.readVInt()
        self.clubLowID = self.readVInt()  # VInt[7]
        
        print(f"[JoinMessage] field0: {field0}")
        print(f"[JoinMessage] field1: {field1}")
        print(f"[JoinMessage] field2: {field2}")
        print(f"[JoinMessage] field3: {field3}")
        print(f"[JoinMessage] field4: {field4}")
        print(f"[JoinMessage] field5: {field5}")
        print(f"[JoinMessage] field6: {field6}")
        print(f"[JoinMessage] clubLowID: {self.clubLowID}")

    def execute(self, calling_instance, fields, cryptoInit):
        player = calling_instance.player
        
        # Usa clubLowID dal decode, non da player.ClubLowID
        clubLowID = self.clubLowID
        
        # DEBUG: Mostra clubLowID che usiamo
        print(f"[JoinMessage] Using clubLowID: {clubLowID} for player {player.LowID}")
        
        # Ruolo base quando entra in un club
        player.ClubRole = 1

        # Verifica che l'alliance esista
        alliance_data = player.alliance_db.getAlliance(clubLowID)
        if alliance_data is None:
            print(f"[JoinMessage] ERROR: Club {clubLowID} not found")
            # Club non esistente → reset stato alliance e uscita
            player.IsInAlliance = False
            player.ClubLowID = 0
            return

        print(f"[JoinMessage] Club found: {alliance_data['name']} (ID: {clubLowID})")

        # Se il player era già in un'altra alliance, rimuovilo da lì
        if player.IsInAlliance and player.ClubLowID != clubLowID:
            # Rimuovi player dal vecchio club
            player.alliance_db.removeMember(player.LowID, player.ClubLowID)
            print(f"[JoinMessage] Player removed from old club {player.ClubLowID}")

        # Aggiungi il player come membro nel DB
        result = player.alliance_db.addMember(
            player_id=player.LowID,
            alliance_id=clubLowID,
            club_role=player.ClubRole
        )
        
        if result:
            print(f"[JoinMessage] Member added: player {player.LowID} to club {clubLowID}")
        else:
            print(f"[JoinMessage] ERROR: Failed to add member to club {clubLowID}")

        # Setta player.ClubLowID ORA dopo addMember successo
        player.ClubLowID = clubLowID
        player.IsInAlliance = True
        print(f"[JoinMessage] Set player.ClubLowID = {player.ClubLowID}")

        # Ricarica i dati alliance dal DB nel player
        player.load_alliance()
        print(f"[JoinMessage] After load_alliance: player.ClubLowID = {player.ClubLowID}, IsInAlliance = {player.IsInAlliance}")

        player.add_chat_message(
            player_name=player.Name,
            player_role=player.ClubRole,
            event_type=3,   
            tick=0,
            message=""
        )

        # Messaggi verso il client
        if fields is None:
            fields = {}
        fields["Socket"] = player.client
        
        print(f"[JoinMessage] Sending messages 24333 and 24399 to client")
        Messaging.sendMessage(24333, fields, cryptoInit, player, calling_instance)
        Messaging.sendMessage(24399, fields, cryptoInit, player, calling_instance)
        # AllianceStreamMessage(self.client, self.player, player.ClubLowID, 0).send()

        members = player.alliance_db.getMembers(player.ClubLowID)
        print(f"[JoinMessage] Club has {len(members)} members")
        for m in members:
            pass
            # AllianceChatServerMessage(self.client, player, 3).sendWithLowID(m["player_id"])
        # AllianceMemberEntryMessage(self.client, player).sendToOthers()

    def getMessageType(self):
        return self.id

    def getMessageVersion(self):
        return self.messageVersion