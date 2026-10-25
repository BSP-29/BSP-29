import json
import os
from pathlib import Path
from typing import Optional, Dict, Any


class BanManager:
    """
    Gestisce i ban per IP e per Account (LowID).
    Salva i ban in un file JSON persistente.
    """
    
    def __init__(self, ban_file: str = "data/bans.json"):
        self.ban_file = Path(ban_file)
        self.ban_file.parent.mkdir(parents=True, exist_ok=True)
        self._bans = self._load_bans()
    
    def _load_bans(self) -> Dict[str, Any]:
        """Carica i ban dal file JSON."""
        if self.ban_file.exists():
            try:
                with open(self.ban_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {"ip_bans": {}, "account_bans": {}}
        return {"ip_bans": {}, "account_bans": {}}
    
    def _save_bans(self) -> None:
        """Salva i ban sul file JSON."""
        try:
            with open(self.ban_file, "w", encoding="utf-8") as f:
                json.dump(self._bans, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"[BanManager] Errore nel salvataggio ban: {e}")
    
    # ===== IP BAN =====
    
    def ban_ip(self, ip: str, reason: str = "Banned by admin", banned_by: str = "Console") -> bool:
        """Banna un indirizzo IP."""
        if not self._is_valid_ip(ip):
            print(f"[BanManager] IP non valido: {ip}")
            return False
        
        self._bans["ip_bans"][ip] = {
            "reason": reason,
            "banned_by": banned_by,
            "timestamp": self._get_timestamp()
        }
        self._save_bans()
        print(f"[BanManager] IP bannato: {ip} - Motivo: {reason}")
        return True
    
    def unban_ip(self, ip: str) -> bool:
        """Rimuove il ban da un IP."""
        if ip in self._bans["ip_bans"]:
            del self._bans["ip_bans"][ip]
            self._save_bans()
            print(f"[BanManager] IP sbannato: {ip}")
            return True
        return False
    
    def is_ip_banned(self, ip: str) -> Optional[Dict[str, Any]]:
        """Controlla se un IP è bannato. Restituisce i dettagli del ban o None."""
        return self._bans["ip_bans"].get(ip)
    
    def get_banned_ips(self) -> Dict[str, Any]:
        """Restituisce tutti gli IP bannati."""
        return self._bans["ip_bans"].copy()
    
    # ===== ACCOUNT BAN (per LowID) =====
    
    def ban_account(self, low_id: int, reason: str = "Banned by admin", banned_by: str = "Console") -> bool:
        """Banna un account per LowID."""
        if low_id <= 0:
            print(f"[BanManager] LowID non valido: {low_id}")
            return False
        
        low_id_str = str(low_id)
        self._bans["account_bans"][low_id_str] = {
            "reason": reason,
            "banned_by": banned_by,
            "timestamp": self._get_timestamp()
        }
        self._save_bans()
        print(f"[BanManager] Account bannato: 0-{low_id} - Motivo: {reason}")
        return True
    
    def unban_account(self, low_id: int) -> bool:
        """Rimuove il ban da un account."""
        low_id_str = str(low_id)
        if low_id_str in self._bans["account_bans"]:
            del self._bans["account_bans"][low_id_str]
            self._save_bans()
            print(f"[BanManager] Account sbannato: 0-{low_id}")
            return True
        return False
    
    def is_account_banned(self, low_id: int) -> Optional[Dict[str, Any]]:
        """Controlla se un account è bannato. Restituisce i dettagli del ban o None."""
        return self._bans["account_bans"].get(str(low_id))
    
    def get_banned_accounts(self) -> Dict[str, Any]:
        """Restituisce tutti gli account bannati."""
        return self._bans["account_bans"].copy()
    
    # ===== UTILITY =====
    
    def _is_valid_ip(self, ip: str) -> bool:
        """Valida un indirizzo IPv4."""
        parts = ip.split(".")
        if len(parts) != 4:
            return False
        try:
            return all(0 <= int(part) <= 255 for part in parts)
        except ValueError:
            return False
    
    def _get_timestamp(self) -> int:
        """Restituisce timestamp corrente."""
        import time
        return int(time.time())
    
    def format_ban_list(self) -> str:
        """Formatta la lista dei ban per visualizzazione in console."""
        lines = ["=== BAN LIST ==="]
        
        ip_bans = self._bans["ip_bans"]
        if ip_bans:
            lines.append("\n--- IP BANS ---")
            for ip, data in ip_bans.items():
                lines.append(f"  {ip}: {data['reason']} (by {data['banned_by']})")
        else:
            lines.append("\n--- IP BANS --- (vuoto)")
        
        account_bans = self._bans["account_bans"]
        if account_bans:
            lines.append("\n--- ACCOUNT BANS ---")
            for low_id, data in account_bans.items():
                lines.append(f"  0-{low_id}: {data['reason']} (by {data['banned_by']})")
        else:
            lines.append("\n--- ACCOUNT BANS --- (vuoto)")
        
        return "\n".join(lines)


# Istanza globale
BanManagerInstance = BanManager()