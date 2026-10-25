from Classes.Logic import AllianceChat
from Classes.Packets.PiranhaMessage import PiranhaMessage
from Classes.DB.DynamicDB import DynamicDB
from Classes.Messaging import Messaging

TRANSLATIONS = {
    "IT": {
        "help_title": "📜 COMANDI DISPONIBILI",
        "help_cmd_1": "/help - Mostra questa lista di comandi",
        "help_cmd_2": "/lang IT|EN - Imposta la lingua dei messaggi (IT o EN)",
        "lang_usage": "❌ Usa: /lang IT oppure /lang EN",
        "lang_set": "✅ Lingua impostata su: {langs}",
        "lang_invalid": "❌ Lingua non valida. Usa IT o EN",
        "unknown_cmd": "❌ Comando non riconosciuto: {cmd}. Usa /help per la lista."
    },
    "EN": {
        "help_title": "📜 AVAILABLE COMMANDS",
        "help_cmd_1": "/help - Show this list of commands",
        "help_cmd_2": "/lang IT|EN - Set message language (IT or EN)",
        "lang_usage": "❌ Use: /lang IT or /lang EN",
        "lang_set": "✅ Language set to: {langs}",
        "lang_invalid": "❌ Invalid language. Use IT or EN",
        "unknown_cmd": "❌ Unknown command: {cmd}. Use /help for the list."
    }
}


class ChatToAllianceStreamMessage(PiranhaMessage):
    def __init__(self, messageData):
        super().__init__(messageData)
        self.messageVersion = 0

    # --------- CLIENT -> SERVER ----------
    def decode(self):
        self.msg = self.readString()

    # --------- LINGUA ----------
    def _get_lang_for_player(self, player):
        db = DynamicDB(player_id=str(player.LowID))
        lang = db.get_lang()
        lang = str(lang).upper() if lang is not None else "EN"
        if lang not in ("IT", "EN"):
            lang = "EN"
        return lang, db

    def _t(self, key, lang, **kwargs):
        base = TRANSLATIONS.get(lang, TRANSLATIONS["EN"])
        text = base.get(key, key)
        return text.format(**kwargs) if kwargs else text

    # --------- MESSAGGIO CLUB PER COMANDI ----------
    def _send_command_reply(self, calling_instance, cryptoInit, text):
        player = calling_instance.player

        club_low_id = int(getattr(player, "ClubLowID", 0) or 0)
        if not club_low_id:
            return

        # Command replies go through the same stream as normal chat, so the
        # client renders them identically instead of through a second packet
        # that wrapped its payload in a stray four byte length prefix.
        entry = AllianceChat.add_chat_message(
            club_low_id,
            int(getattr(player, "LowID", 0) or 0),
            str(getattr(player, "Name", "") or ""),
            int(getattr(player, "ClubRole", 1) or 1),
            text,
        )
        self._broadcast_entry(club_low_id, entry)

    def _broadcast_entry(self, club_low_id, entry):
        """Send one 24312 stream entry to every online member of the club."""
        for member in AllianceChat.online_members(club_low_id):
            session = getattr(member, "session", None)
            if session is None or not hasattr(session, "client") or not hasattr(session, "cryptoInit"):
                session = None
                from Classes.ClientsManager import ClientsManager
                data = ClientsManager.GetAll().get(int(getattr(member, "LowID", 0) or 0))
                session = data.get("Session") if data else None
            if session is None or not hasattr(session, "client") or not hasattr(session, "cryptoInit"):
                continue
            Messaging.sendMessage(
                24312,
                {"Socket": session.client, "Entry": entry},
                session.cryptoInit,
                member,
            )

    def _send_chat_message(self, calling_instance, cryptoInit, player, text):
        club_low_id = int(getattr(player, "ClubLowID", 0) or 0)
        if not club_low_id:
            return

        entry = AllianceChat.add_chat_message(
            club_low_id,
            int(getattr(player, "LowID", 0) or 0),
            str(getattr(player, "Name", "") or ""),
            int(getattr(player, "ClubRole", 1) or 1),
            text,
        )
        self._broadcast_entry(club_low_id, entry)

    # --------- LOGICA PRINCIPALE ----------
    def execute(self, calling_instance, fields, cryptoInit):
        player = calling_instance.player
        text = self.msg

        # Ordinary club chat used to be dropped outright: anything that was not
        # a slash command returned here, so the channel never carried a message.
        if not isinstance(text, str) or not text.strip():
            return

        if not text.startswith("/"):
            self._send_chat_message(calling_instance, cryptoInit, player, text)
            return

        lang, db = self._get_lang_for_player(player)

        print("ChatToAllianceStreamMessage created")
        print("--- [ALLIANCE COMMAND] ---")
        print(f"Player ID: {player.ID}")
        print(f"Player Name: {player.Name}")
        print(f"Lang attuale: {lang}")
        print(f"Input: {text}")
        print("--------------------------")

        parts = text.split(" ", 1)
        command = parts[0].lower()
        arg = parts[1].strip() if len(parts) > 1 else None

        if command == "/help":
            line1 = self._t("help_title", lang)
            line2 = self._t("help_cmd_1", lang)
            line3 = self._t("help_cmd_2", lang)
            reply = f"{line1}\n{line2}\n{line3}"
            print(reply)
            self._send_command_reply(calling_instance, cryptoInit, reply)
            return

        if command == "/lang":
            if not arg:
                reply = self._t("lang_usage", lang)
                print(reply)
                self._send_command_reply(calling_instance, cryptoInit, reply)
                return

            new_lang = arg.upper()
            if new_lang not in ("IT", "EN"):
                reply = self._t("lang_invalid", lang)
                print(reply)
                self._send_command_reply(calling_instance, cryptoInit, reply)
                return

            db.set_lang(new_lang)
            lang = new_lang

            reply = self._t("lang_set", lang, langs=new_lang)
            print(reply)
            self._send_command_reply(calling_instance, cryptoInit, reply)
            return

        reply = self._t("unknown_cmd", lang, cmd=command)
        print(reply)
        self._send_command_reply(calling_instance, cryptoInit, reply)

    def getMessageType(self):
        return 14315

    def getMessageVersion(self):
        return self.messageVersion