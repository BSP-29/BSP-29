from Classes.Messaging import Messaging
from Classes.Packets.PiranhaMessage import PiranhaMessage
from Classes.DB.DynamicDB import DynamicDB
from Classes.TeamManager import get_member_record, get_room_players
from Classes.Packets.Server.Home.TeamStream2 import room_id_for

TRANSLATIONS = {
    "IT": {
        "help_title": "📜 COMANDI DISPONIBILI",
        "help_cmd_1": "/help - Mostra questa lista di comandi",
        "help_cmd_2": "/lang IT|EN - Imposta la lingua dei messaggi (IT o EN)",
        "help_cmd_3": "/refresh - Ricarica il client (dopo aver usato la chat comandi il gioco potrebbe crashare, è normale)",
        "help_cmd_4": "/register USER PASS - Registra l'account con un username e una password",
        "help_cmd_5": "/login USER PASS - Accedi a un account registrato da qualsiasi device",

        "lang_usage": "❌ Usa: /lang IT oppure /lang EN",
        "lang_set": "✅ Lingua impostata su: {langs}",
        "lang_invalid": "❌ Lingua non valida. Usa IT o EN",

        "unknown_cmd": "❌ Comando non riconosciuto: {cmd}. Usa /help per la lista.",

        "refresh_ok": "🔄 Client in refresh... dopo aver usato la chat comandi è normale dover riavviare il gioco.",

        "register_usage": "❌ Usa: /register USERNAME PASSWORD",
        "register_already": "❌ Questo account è già registrato come: {user}",
        "register_ok": "✅ Registrazione completata. Username: {user}",

        "login_usage": "❌ Usa: /login USERNAME PASSWORD",
        "login_not_found": "❌ Nessun account registrato per questo profilo.",
        "login_wrong_user": "❌ L'username non corrisponde a quello registrato: {user}",
        "login_wrong_pass": "❌ Password errata per l'username: {user}",
        "login_ok": "✅ Login effettuato come: {user}",

        "help_cmd_6": "/ready - Segna lo stato pronto e avvia la ricerca",
        "ready_usage": "❌ Usa: /ready on|off",
        "ready_on": "✅ Sei pronto. In attesa che tutti siano pronti.",
        "ready_off": "✅ Non sei più pronto.",
    },
    "EN": {
        "help_title": "📜 AVAILABLE COMMANDS",
        "help_cmd_1": "/help - Show this list of commands",
        "help_cmd_2": "/lang IT|EN - Set message language (IT or EN)",
        "help_cmd_3": "/refresh - Reload the client (after using the command chat the game may crash, this is expected)",
        "help_cmd_4": "/register USER PASS - Register your account with a username and password",
        "help_cmd_5": "/login USER PASS - Log into a registered account from any device",

        "lang_usage": "❌ Use: /lang IT or /lang EN",
        "lang_set": "✅ Language set to: {langs}",
        "lang_invalid": "❌ Invalid language. Use IT or EN",

        "unknown_cmd": "❌ Unknown command: {cmd}. Use /help for the list.",

        "refresh_ok": "🔄 Client refreshing... after using the command chat it is normal that you need to restart the game.",

        "register_usage": "❌ Use: /register USERNAME PASSWORD",
        "register_already": "❌ This profile is already registered as: {user}",
        "register_ok": "✅ Registration completed. Username: {user}",

        "login_usage": "❌ Use: /login USERNAME PASSWORD",
        "login_not_found": "❌ No registered account for this profile.",
        "login_wrong_user": "❌ Username does not match the registered one: {user}",
        "login_wrong_pass": "❌ Wrong password for username: {user}",
        "login_ok": "✅ Logged in as: {user}",

        "help_cmd_6": "/ready - Set your ready state and start the search",
        "ready_usage": "❌ Use: /ready on|off",
        "ready_on": "✅ You are ready. Waiting for everyone else.",
        "ready_off": "✅ You are no longer ready.",
    }
}


class TeamChat(PiranhaMessage):
    def __init__(self, messageData):
        super().__init__(messageData)
        self.message = ""
        self.messageVersion = 0
        
    def decode(self):
        # The reference reads the string and nothing else. The extra VInt that
        # used to follow it consumed a byte the client never sent.
        self.message = self.readString()
        return {}
    
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

    def _send_team_message(self, fields, cryptoInit, player, text):
        """Publish to the team stream and fan it out to every member.

        The entry is appended once, with the sender as the author, and the same
        stream is then built for every socket. Appending from inside the encoder
        would add one copy per recipient and attribute the line to whichever
        member happened to be first in the list.
        """
        from Classes.Packets.Server.Home.TeamStream2 import add_room_chat_entry

        room_id = room_id_for(player)
        fields["Message"] = text

        recipients = get_room_players(room_id)
        if not recipients:
            recipients = [player]

        add_room_chat_entry(room_id, player, text)

        for member in recipients:
            session = getattr(member, "session", None)
            if not session or not hasattr(session, "client") or not hasattr(session, "cryptoInit"):
                continue
            Messaging.sendMessage(
                24131,
                {"Socket": session.client, "Message": text},
                session.cryptoInit,
                member,
            )

    def _broadcast_team_snapshot(self, cryptoInit, player):
        """Re-send the room snapshot so clients agree on roster and ready state.

        Members that already have a battle session are skipped, so a chat message
        cannot pull a client off the loading screen with a stale lobby snapshot.
        """
        from Classes.TeamMatchmaking import broadcast_team
        broadcast_team(room_id_for(player))

    def _send_outofsync(self, calling_instance, cryptoInit, player):
        # 24104 = OutOfSync
        Messaging.sendMessage(
            24104,
            {
                "Socket": calling_instance.client,
                "Tick": 0,
                "ServerChecksum": 0,
                "ClientChecksum": 0
            },
            cryptoInit,
            player
        )

    def _split_two_args(self, arg: str):
        if not arg:
            return None, None
        parts = arg.split(" ", 1)
        if len(parts) < 2:
            return None, None
        return parts[0].strip(), parts[1].strip()

    def execute(self, calling_instance, fields, cryptoInit):
        if fields is None:
            fields = {}
        fields["Socket"] = calling_instance.client

        text = self.message
        player = calling_instance.player

        # Messaggio normale: invia come prima
        if not isinstance(text, str) or not text.startswith("/"):
            self._send_team_message(fields, cryptoInit, player, text)
            return

        # Da qui: è un comando
        lang, db = self._get_lang_for_player(player)

        print("TeamChat command detected")
        print(f"Player ID: {player.ID}")
        print(f"Player Name: {player.Name}")
        print(f"Lang: {lang}")
        print(f"Input: {text}")

        parts = text.split(" ", 1)
        command = parts[0].lower()
        arg = parts[1].strip() if len(parts) > 1 else None

        # /help
        if command == "/help":
            line1 = self._t("help_title", lang)
            line2 = self._t("help_cmd_1", lang)
            line3 = self._t("help_cmd_2", lang)
            line4 = self._t("help_cmd_3", lang)
            line5 = self._t("help_cmd_4", lang)
            line6 = self._t("help_cmd_5", lang)
            line7 = self._t("help_cmd_6", lang)
            reply = f"{line1}\n{line2}\n{line3}\n{line4}\n{line5}\n{line6}\n{line7}"
            self._send_team_message(fields, cryptoInit, player, reply)
            return

        # /lang
        if command == "/lang":
            if not arg:
                reply = self._t("lang_usage", lang)
                self._send_team_message(fields, cryptoInit, player, reply)
                return

            new_lang = arg.upper()
            if new_lang not in ("IT", "EN"):
                reply = self._t("lang_invalid", lang)
                self._send_team_message(fields, cryptoInit, player, reply)
                return

            db.set_lang(new_lang)
            lang = new_lang

            reply = self._t("lang_set", lang, langs=new_lang)
            self._send_team_message(fields, cryptoInit, player, reply)
            return

        # /register USER PASS
        if command == "/register":
            user, pwd = self._split_two_args(arg)
            if not user or not pwd:
                reply = self._t("register_usage", lang)
                self._send_team_message(fields, cryptoInit, player, reply)
                return

            # DB del player corrente
            current_user = db.get_user()
            current_pass = db.get_pass()
            current_registered = db.get_registered()

            # Tratta i valori di default come "non registrato"
            is_default_creds = (current_user == "BSP" and current_pass == "Password")

            if current_registered and not is_default_creds:
                reply = self._t("register_already", lang, user=current_user)
                self._send_team_message(fields, cryptoInit, player, reply)
                return

            db.set_user(user)
            db.set_pass(pwd)
            db.set_registered(True)

            reply = self._t("register_ok", lang, user=user)
            self._send_team_message(fields, cryptoInit, player, reply)
            return

        # /login USER PASS
        if command == "/login":
            user, pwd = self._split_two_args(arg)
            if not user or not pwd:
                reply = self._t("login_usage", lang)
                self._send_team_message(fields, cryptoInit, player, reply)
                return

            # cerca tra TUTTI gli account
            target_low_id = DynamicDB.find_lowid_by_credentials(user, pwd)
            if target_low_id is None:
                reply = self._t("login_not_found", lang)
                self._send_team_message(fields, cryptoInit, player, reply)
                return

            # Carica il DB dell'account trovato
            target_db = DynamicDB(player_id=str(target_low_id))

            # ✅ NON cloniamo credenziali da nessuna parte.
            # Switchiamo semplicemente il player runtime su quell'account.
            calling_instance.player.LowID = target_low_id
            calling_instance.player.ID = [0, target_low_id]
            calling_instance.player.Name = target_db.get_name()

            # NON fare più:
            # db.set_user(user)
            # db.set_pass(pwd)
            # db.set_registered(True)

            reply = self._t("login_ok", lang, user=user)
            self._send_team_message(fields, cryptoInit, calling_instance.player, reply)
            return

        # /ready on|off
        if command == "/ready":
            room_id = room_id_for(player)
            if not room_id:
                self._send_team_message(
                    fields, cryptoInit, player,
                    self._t("ready_usage", lang),
                )
                return

            member_record = get_member_record(room_id, getattr(player, "LowID", 0))
            if member_record is None:
                self._send_team_message(
                    fields, cryptoInit, player,
                    self._t("ready_usage", lang),
                )
                return

            wanted = True
            if arg:
                lowered = arg.strip().lower()
                if lowered in ("off", "no", "0", "false", "notready", "not"):
                    wanted = False
                elif lowered not in ("on", "yes", "1", "true", "ready", "si", "sì"):
                    self._send_team_message(
                        fields, cryptoInit, player,
                        self._t("ready_usage", lang),
                    )
                    return

            player.isReady = wanted
            member_record["READY"] = wanted
            self._broadcast_team_snapshot(cryptoInit, player)
            self._send_team_message(
                fields, cryptoInit, player,
                self._t("ready_on" if wanted else "ready_off", lang),
            )
            return

        # /refresh
        if command == "/refresh":
            reply = self._t("refresh_ok", lang)
            self._send_team_message(fields, cryptoInit, player, reply)
            self._send_outofsync(calling_instance, cryptoInit, player)
            return

        # Comando sconosciuto
        reply = self._t("unknown_cmd", lang, cmd=command)
        self._send_team_message(fields, cryptoInit, player, reply)

    def getMessageType(self):
        return 14359

    def getMessageVersion(self):
        return self.messageVersion