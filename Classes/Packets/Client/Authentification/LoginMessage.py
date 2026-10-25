from Classes.Messaging import Messaging
from Classes.Packets.PiranhaMessage import PiranhaMessage
from Classes.ClientsManager import ClientsManager
from Classes.DB.DynamicDB import DynamicDB as DB
from Classes.Instances.Classes.Player import Player
from Classes.BanManager import BanManagerInstance
import zlib


class LoginMessage(PiranhaMessage):
    def __init__(self, messageData):
        super().__init__(messageData)
        self.messageVersion = 0

    def encode(self, fields):
        pass

    def decode(self):
        fields = {}
        fields["AccountID"] = self.readLong()
        fields["PassToken"] = self.readString()
        fields["ClientMajor"] = self.readInt()
        fields["ClientMinor"] = self.readInt()
        fields["ClientBuild"] = self.readInt()
        fields["ResourceSha"] = self.readString()
        fields["Device"] = self.readString()
        fields["PreferredLanguage"] = self.readDataReference()
        fields["PreferredDeviceLanguage"] = self.readString()
        fields["OSVersion"] = self.readString()
        fields["isAndroid"] = self.readBoolean()
        fields["IMEI"] = self.readString()
        fields["AndroidID"] = self.readString()
        fields["isAdvertisingEnabled"] = self.readBoolean()
        fields["AppleIFV"] = self.readString()
        fields["RndKey"] = self.readInt()
        fields["AppStore"] = self.readVInt()
        fields["ClientVersion"] = self.readString()
        fields["TencentOpenId"] = self.readString()
        fields["TencentToken"] = self.readString()
        fields["TencentPlatform"] = self.readVInt()
        fields["DeviceVerifierResponse"] = self.readString()
        fields["AppLicensingSignature"] = self.readString()
        fields["DeviceVerifierResponse2"] = self.readString()

        try:
            fields["SupercellIdToken"] = self.readCompressedString()
        except Exception:
            fields["SupercellIdToken"] = ""

        fields["UpdateMaintenanceMode"] = self.readBoolean()
        fields["YoozooOsdkTicket"] = self.readString()
        fields["YoozooDeviceId"] = self.readString()
        super().decode(fields)
        return fields

    def execute(message, calling_instance, fields, cryptoInit):
        if fields["ClientMajor"] != 29:
            Messaging.sendMessage(20103, {
                "Socket": calling_instance.client,
                "ErrorID": 16,
                "FingerprintData": "{}",
                "ContentURL": "https://t.me/BrawlStarsProjects",
                "Message": "Ops! Wrong version; Check updates on t.me/BrawlStarsProjects"
            }, cryptoInit)
            return

        scid_token = fields.get("SupercellIdToken", "")
        scid_token = scid_token if isinstance(scid_token, str) else str(scid_token)

        if scid_token:
            target_low_id = DB.find_lowid_by_token(scid_token)
            if target_low_id is None:
                db_manager = DB("0")
                new_id_str = db_manager.create_account()
                target_low_id = int(new_id_str)
                DB.reassign_token_to_lowid(scid_token, target_low_id)
                print(f"[SCID REG] Creato 0-{target_low_id} per token completo")
            else:
                print(f"[SCID LOGIN] Caricato 0-{target_low_id} per token completo")
        else:
            target_low_id = 0
            print("[GUEST] Token vuoto: Accesso all'account comune 0-0")

        calling_instance.player = Player(low_id=target_low_id)
        # FIX: assegna il client al player immediatamente
        calling_instance.player.client = calling_instance.client
        calling_instance.player.session = calling_instance
        calling_instance.cryptoInit = cryptoInit

        # === CONTROLLO ACCOUNT BAN ===
        if target_low_id > 0:
            account_ban = BanManagerInstance.is_account_banned(target_low_id)
            if account_ban:
                ban_reason = account_ban.get('reason', '') if account_ban.get('reason') else "You got Banned"
                print(f"[BAN] Login rifiutato per account bannato: 0-{target_low_id} - Motivo: {ban_reason}")
                Messaging.sendMessage(20103, {
                    "Socket": calling_instance.client,
                    "ErrorID": 11,  # Ban error code
                    "FingerprintData": "{}",
                    "ContentURL": "",
                    "Message": ban_reason
                }, cryptoInit)
                return

        calling_instance.player.Token = ""
        fields["ServerPassToken"] = ""

        calling_instance.player.ClientVersion = f'{fields["ClientMajor"]}.{fields["ClientBuild"]}.{fields["ClientMinor"]}'
        fields["Socket"] = calling_instance.client

        ClientsManager.AddPlayer(target_low_id, calling_instance.client, calling_instance)

        Messaging.sendMessage(20104, fields, cryptoInit, calling_instance.player)
        Messaging.sendMessage(24101, fields, cryptoInit, calling_instance.player)
        Messaging.sendMessage(24399, fields, cryptoInit, calling_instance.player)
        # The client expects its friend list as part of the initial lobby load.
        Messaging.sendMessage(20105, fields, cryptoInit, calling_instance.player)

        # Restore the persisted team in the client's lobby after reconnect.
        player = calling_instance.player
        team_id = player.TeamID[1] if player.TeamID and len(player.TeamID) > 1 else 0
        if team_id:
            from Classes.TeamManager import get_room_players
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

    def getMessageType(self):
        return 10101

    def getMessageVersion(self):
        return self.messageVersion
