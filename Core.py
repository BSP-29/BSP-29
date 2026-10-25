import os
import signal
import threading

import Configuration
from Classes.BanManager import BanManagerInstance
from Classes.BattleServer import start_udp_listener
from Classes.ConsoleIO import STDIN_QUEUE, CONSOLE_PAUSED
from Classes.ServerConnection import ServerConnection
from Classes.Messaging import Messaging
from Classes.ClientsManager import ClientsManager


def stop_process_on_ctrl_c(_signum, _frame):
    os._exit(130)


def _console_reader():
    while True:
        try:
            line = input()
        except (EOFError, OSError):
            break
        if CONSOLE_PAUSED.is_set():
            STDIN_QUEUE.put(line)
        else:
            _handle_console_command(line)


def _handle_console_command(cmd):
    cmd = cmd.strip()
    if not cmd:
        return
    if cmd.upper() in ("Y", "N", "YES", "NO", "S", "SI", "SÌ"):
        return
    if cmd == "/clearpass":
        _clearpass()
    elif cmd.startswith("/clearpass "):
        parts = cmd.split(" ", 1)
        if len(parts) > 1:
            _clearpass(parts[1])
    elif cmd.startswith("/ban "):
        _handle_ban_command(cmd)
    elif cmd == "/banlist":
        print(BanManagerInstance.format_ban_list())
    elif cmd.startswith("/unban "):
        _handle_unban_command(cmd)
    elif cmd.startswith("/add "):
        _handle_add_command(cmd)
    elif cmd.startswith("/activatepass "):
        _handle_activate_pass_command(cmd)
    elif cmd.startswith("/revokepass "):
        _handle_revoke_pass_command(cmd)
    elif cmd.startswith("/allowmultitier "):
        _handle_allow_multitier_command(cmd)
    elif cmd.startswith("/revokemultitier "):
        _handle_revoke_multitier_command(cmd)
    else:
        print(f"[CONSOLE] Unknown command: {cmd}")


def _send_out_of_sync_to_player(low_id: int):
    """Invia OutOfSyncMessage (24104) a un giocatore connesso per disconnetterlo."""
    all_players = ClientsManager.GetAll()
    if low_id not in all_players:
        return False
    
    player_data = all_players[low_id]
    socket = player_data.get("Socket")
    session = player_data.get("Session")
    
    if not socket or not session:
        return False
    
    try:
        crypto = getattr(session, "cryptoInit", None)
        player = getattr(session, "player", None)
        
        Messaging.sendMessage(
            24104,
            {
                "Socket": socket,
                "Tick": 0,
                "ServerChecksum": 0,
                "ClientChecksum": 0,
            },
            crypto,
            player,
        )
        print(f"[CONSOLE] OutOfSyncMessage inviato a 0-{low_id}")
        return True
    except Exception as e:
        print(f"[CONSOLE] Errore invio OutOfSyncMessage a 0-{low_id}: {e}")
        return False


def _handle_ban_command(cmd):
    """Gestisce il comando /ban <ip|lowid> [motivo]"""
    parts = cmd.split(" ", 2)
    if len(parts) < 2:
        print("[CONSOLE] Uso: /ban <ip|lowid> [motivo]")
        print("[CONSOLE] Esempi:")
        print("  /ban 192.168.1.100 Cheating")
        print("  /ban 18 Hacking")
        print("  /ban 0-18 Hacking")
        return
    
    target = parts[1]
    reason = parts[2] if len(parts) > 2 else ""
    
    target_type, target_value = _parse_target(target)
    
    if target_type == 'ip':
        success = BanManagerInstance.ban_ip(target_value, reason, "Console")
        if success:
            msg = f"IP {target_value} bannato"
            if reason:
                msg += f": {reason}"
            else:
                msg += " (messaggio: You got Banned)"
            print(f"[CONSOLE] {msg}")
            # Disconnetti giocatori connessi da quell'IP
            _kick_players_by_ip(target_value)
        else:
            print(f"[CONSOLE] Errore: IP non valido: {target_value}")
    elif target_type == 'account':
        success = BanManagerInstance.ban_account(target_value, reason, "Console")
        if success:
            msg = f"Account 0-{target_value} bannato"
            if reason:
                msg += f": {reason}"
            else:
                msg += " (messaggio: You got Banned)"
            print(f"[CONSOLE] {msg}")
            # Se il giocatore è online, mandagli OutOfSyncMessage
            _send_out_of_sync_to_player(target_value)
        else:
            print(f"[CONSOLE] Errore: LowID non valido: {target_value}")
    else:
        print(f"[CONSOLE] Errore: '{target}' non è un IP valido né un LowID numerico (usa formato: 18 o 0-18)")


def _handle_unban_command(cmd):
    """Gestisce il comando /unban <ip|lowid>"""
    parts = cmd.split(" ")
    if len(parts) < 2:
        print("[CONSOLE] Uso: /unban <ip|lowid>")
        print("[CONSOLE] Esempi:")
        print("  /unban 192.168.1.100")
        print("  /unban 18")
        print("  /unban 0-18")
        return
    
    target = parts[1]
    target_type, target_value = _parse_target(target)
    
    if target_type == 'ip':
        success = BanManagerInstance.unban_ip(target_value)
        if success:
            print(f"[CONSOLE] IP {target_value} sbannato")
        else:
            print(f"[CONSOLE] IP {target_value} non era bannato")
    elif target_type == 'account':
        success = BanManagerInstance.unban_account(target_value)
        if success:
            print(f"[CONSOLE] Account 0-{target_value} sbannato")
        else:
            print(f"[CONSOLE] Account 0-{target_value} non era bannato")
    else:
        print(f"[CONSOLE] Errore: '{target}' non è un IP valido né un LowID numerico (usa formato: 18 o 0-18)")


def _handle_add_command(cmd):
    """Gestisce il comando /add <0-ID|ID> <amount> <type>.
    Types: Gems, BPTokens, TokenMultiplier, Starpoints, Trophies
    Amount negativo rimuove.
    Esempi:
      /add 18 1000 Gems
      /add 0-18 -500 Trophies
      /add 18 10 BPTokens
    """
    parts = cmd.split(" ")
    if len(parts) < 4:
        print("[CONSOLE] Uso: /add <0-ID|ID> <amount> <Gems|BPTokens|TokenMultiplier|Starpoints|Trophies>")
        print("[CONSOLE] Amount negativo per rimuovere")
        return
    
    target = parts[1]
    target_type, target_value = _parse_target(target)
    
    if target_type != 'account':
        print(f"[CONSOLE] Errore: '{target}' non è un LowID valido (usa formato: 18 o 0-18)")
        return
    
    try:
        amount = int(parts[2])
    except ValueError:
        print(f"[CONSOLE] Errore: amount '{parts[2]}' non valido")
        return
    
    resource_type = parts[3].lower()
    valid_types = ['gems', 'bptokens', 'tokenmultiplier', 'starpoints', 'trophies']
    if resource_type not in valid_types:
        print(f"[CONSOLE] Errore: tipo '{parts[3]}' non valido. Usa: {', '.join(valid_types)}")
        return
    
    from Classes.DB.DynamicDB import DynamicDB
    db = DynamicDB(str(target_value))
    
    try:
        if resource_type == 'gems':
            new_val = db.add_gems(amount)
            print(f"[CONSOLE] Gems per 0-{target_value}: {new_val} (cambiamento: {amount:+d})")
        elif resource_type == 'bptokens':
            new_val = db.add_brawl_pass_tokens(amount)
            print(f"[CONSOLE] BPTokens per 0-{target_value}: {new_val} (cambiamento: {amount:+d})")
        elif resource_type == 'tokenmultiplier':
            new_val = db.add_tokens_doubler(amount)
            print(f"[CONSOLE] TokenMultiplier per 0-{target_value}: {new_val} (cambiamento: {amount:+d})")
        elif resource_type == 'starpoints':
            new_val = db.add_star_points(amount)
            print(f"[CONSOLE] StarPoints per 0-{target_value}: {new_val} (cambiamento: {amount:+d})")
        elif resource_type == 'trophies':
            new_val = db.add_total_trophies(amount)
            print(f"[CONSOLE] Trophies (brawler selezionato) per 0-{target_value}: {new_val} (cambiamento: {amount:+d})")
    except Exception as e:
        print(f"[CONSOLE] Errore: {e}")
        return
    
    # Manda OutOfSyncMessage se il giocatore è online
    _send_out_of_sync_to_player(target_value)


def _handle_activate_pass_command(cmd):
    """Gestisce il comando /activatepass <0-ID|ID> per attivare il Brawl Pass premium."""
    parts = cmd.split(" ")
    if len(parts) < 2:
        print("[CONSOLE] Uso: /activatepass <0-ID|ID>")
        print("[CONSOLE] Esempio: /activatepass 18  oppure  /activatepass 0-18")
        return
    
    target = parts[1]
    target_type, target_value = _parse_target(target)
    
    if target_type != 'account':
        print(f"[CONSOLE] Errore: '{target}' non è un LowID valido (usa formato: 18 o 0-18)")
        return
    
    from Classes.DB.DynamicDB import DynamicDB
    db = DynamicDB(str(target_value))
    db.set_brawl_pass_bought(True)
    print(f"[CONSOLE] Brawl Pass premium ATTIVATO per account 0-{target_value}")
    # Manda OutOfSyncMessage se il giocatore è online
    _send_out_of_sync_to_player(target_value)


def _handle_revoke_pass_command(cmd):
    """Gestisce il comando /revokepass <0-ID|ID> per revocare il Brawl Pass premium."""
    parts = cmd.split(" ")
    if len(parts) < 2:
        print("[CONSOLE] Uso: /revokepass <0-ID|ID>")
        print("[CONSOLE] Esempio: /revokepass 18  oppure  /revokepass 0-18")
        return
    
    target = parts[1]
    target_type, target_value = _parse_target(target)
    
    if target_type != 'account':
        print(f"[CONSOLE] Errore: '{target}' non è un LowID valido (usa formato: 18 o 0-18)")
        return
    
    from Classes.DB.DynamicDB import DynamicDB
    db = DynamicDB(str(target_value))
    db.set_brawl_pass_bought(False)
    print(f"[CONSOLE] Brawl Pass premium REVOCATO per account 0-{target_value}")
    # Manda OutOfSyncMessage se il giocatore è online
    _send_out_of_sync_to_player(target_value)


def _handle_allow_multitier_command(cmd):
    """Gestisce il comando /allowmultitier <0-ID|ID> per abilitare il multi-tier claim."""
    parts = cmd.split(" ")
    if len(parts) < 2:
        print("[CONSOLE] Uso: /allowmultitier <0-ID|ID>")
        print("[CONSOLE] Esempio: /allowmultitier 18  oppure  /allowmultitier 0-18")
        return
    
    target = parts[1]
    target_type, target_value = _parse_target(target)
    
    if target_type != 'account':
        print(f"[CONSOLE] Errore: '{target}' non è un LowID valido (usa formato: 18 o 0-18)")
        return
    
    from Classes.DB.DynamicDB import DynamicDB
    db = DynamicDB(str(target_value))
    db.set_can_multi_tier(True)
    print(f"[CONSOLE] CanMultiTier ABILITATO per account 0-{target_value} (claim duplicati permessi)")


def _handle_revoke_multitier_command(cmd):
    """Gestisce il comando /revokemultitier <0-ID|ID> per disabilitare il multi-tier claim."""
    parts = cmd.split(" ")
    if len(parts) < 2:
        print("[CONSOLE] Uso: /revokemultitier <0-ID|ID>")
        print("[CONSOLE] Esempio: /revokemultitier 18  oppure  /revokemultitier 0-18")
        return
    
    target = parts[1]
    target_type, target_value = _parse_target(target)
    
    if target_type != 'account':
        print(f"[CONSOLE] Errore: '{target}' non è un LowID valido (usa formato: 18 o 0-18)")
        return
    
    from Classes.DB.DynamicDB import DynamicDB
    db = DynamicDB(str(target_value))
    db.set_can_multi_tier(False)
    print(f"[CONSOLE] CanMultiTier DISABILITATO per account 0-{target_value} (claim duplicati non permessi)")


def _is_ip_address(text: str) -> bool:
    """Controlla se una stringa è un indirizzo IPv4."""
    parts = text.split(".")
    if len(parts) != 4:
        return False
    try:
        return all(0 <= int(part) <= 255 for part in parts)
    except ValueError:
        return False


def _parse_target(target: str):
    """
    Parsa il target del comando ban/unban.
    Supporta: IP (192.168.1.1), LowID (18), LowID con prefisso (0-18).
    Restituisce (type, value) dove type è 'ip' o 'account', o (None, None) se invalido.
    """
    # Prima controlla se è un IP
    if _is_ip_address(target):
        return 'ip', target
    
    # Poi prova come LowID (con o senza prefisso "0-")
    clean_target = target
    if target.startswith("0-"):
        clean_target = target[2:]
    
    try:
        low_id = int(clean_target)
        if low_id > 0:
            return 'account', low_id
    except ValueError:
        pass
    
    return None, None


def _kick_players_by_ip(ip: str):
    """Disconnette tutti i giocatori connessi da un IP bannato mandando OutOfSyncMessage."""
    all_players = ClientsManager.GetAll()
    for low_id, data in all_players.items():
        socket = data.get("Socket")
        session = data.get("Session")
        if socket and session:
            try:
                peer = socket.getpeername()
                if peer[0] == ip:
                    crypto = getattr(session, "cryptoInit", None)
                    player = getattr(session, "player", None)
                    Messaging.sendMessage(
                        24104,
                        {
                            "Socket": socket,
                            "Tick": 0,
                            "ServerChecksum": 0,
                            "ClientChecksum": 0,
                        },
                        crypto,
                        player,
                    )
                    print(f"[CONSOLE] OutOfSyncMessage inviato a 0-{low_id} (IP bannato: {ip})")
            except Exception:
                pass


def _clearpass(target_id: str = None):
    """
    Reset coins, gems, brawl pass claims e tokens per un account specifico o per tutti.
    Uso: /clearpass [0-ID|ID]
    Esempi:
      /clearpass          - Non fa nulla (richiesto argomento)
      /clearpass 18       - Reset account 0-18
      /clearpass 0-18     - Reset account 0-18
    """
    import glob
    import json
    import os
    
    if target_id is None:
        print("[CONSOLE] Uso: /clearpass <0-ID|ID>")
        print("[CONSOLE] Esempio: /clearpass 18  oppure  /clearpass 0-18")
        return
    
    # Parsa il target (supporta 18 o 0-18)
    clean_id = target_id
    if target_id.startswith("0-"):
        clean_id = target_id[2:]
    
    try:
        low_id = int(clean_id)
        if low_id <= 0:
            print("[CONSOLE] Errore: LowID deve essere > 0")
            return
    except ValueError:
        print(f"[CONSOLE] Errore: '{target_id}' non è un LowID valido")
        return
    
    base_dir = "data/dynamic"
    fpath = os.path.join(base_dir, f"0-{low_id}.json")
    
    if not os.path.exists(fpath):
        print(f"[CONSOLE] Account 0-{low_id} non trovato")
        return
    
    try:
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"[CONSOLE] Errore lettura {fpath}: {e}")
        return
    
    # Reset coins e gems
    data["Coins"] = 0
    data["Gems"] = 0
    data["StarPoints"] = 0
    data["TokensDoubler"] = 0
    
    # Reset Brawl Pass tokens
    data["BPTOKEN"] = 0
    
    # Rimuovi chiavi Brawl Pass e Trophy Road
    keys_to_remove = [k for k in data.keys()
                      if k.startswith("BrawlPassPremium_S")
                      or k.startswith("BrawlPassFree_S")
                      or k.startswith("TrophyRoadClaimed_S")
                      or k == "BrawlPassBought"
                      or k == "TrophyRoadClaimed"
                      or k == "BrawlPassPremium"
                      or k == "BrawlPassFree"]
    
    for k in keys_to_remove:
        del data[k]
    
    try:
        with open(fpath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"[CONSOLE] /clearpass: account 0-{low_id} resettato (coins=0, gems=0, BPTOKEN=0, claims reset)")
    except Exception as e:
        print(f"[CONSOLE] Errore salvataggio {fpath}: {e}")
        return
    
    # Se il giocatore è online, manda OutOfSyncMessage per disconnetterlo
    _send_out_of_sync_to_player(low_id)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, stop_process_on_ctrl_c)
    start_udp_listener()
    reader = threading.Thread(target=_console_reader, daemon=True)
    reader.start()
    print("[CONSOLE] Commands:")
    print("  /clearpass [0-ID|ID]          - Reset coins/gems/BPTOKEN/claims per un account (es. /clearpass 18)")
    print("  /ban <ip|lowid> [motivo]      - Banna IP (es. 192.168.1.1) o Account (es. 18)")
    print("  /unban <ip|lowid>             - Rimuove ban da IP o Account")
    print("  /banlist                      - Mostra tutti i ban attivi")
    print("  /add <0-ID|ID> <amt> <tipo>   - Add/remove risorse: Gems, BPTokens, TokenMultiplier, StarPoints, Trophies")
    print("  /activatepass <0-ID|ID>       - Attiva Brawl Pass premium (es. /activatepass 18)")
    print("  /revokepass <0-ID|ID>         - Revoca Brawl Pass premium (es. /revokepass 18)")
    print("  /allowmultitier <0-ID|ID>     - Abilita claim duplicati tier (es. /allowmultitier 18)")
    print("  /revokemultitier <0-ID|ID>    - Disabilita claim duplicati tier (es. /revokemultitier 18)")
    print("  (Y/N during prompts are not commands)")
    from Classes.ServerConnection import ServerConnection
    ServerConnection((
        Configuration.settings.get("TCPHost", "0.0.0.0"),
        int(Configuration.settings.get("TCPPort", 9339)),
    ))
