import json
import os
from pathlib import Path
import glob
from typing import Optional


class DynamicDB:
    def __init__(self, player_id: str = "0", base_dir: str = "data/dynamic"):
        self.base_path = Path(base_dir)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.player_id = str(player_id)
        self.metadata_path = self.base_path / "__metadata__.json"

        if self.player_id == "0":
            self._init_metadata()

    def _init_metadata(self):
        if not self.metadata_path.exists():
            with open(self.metadata_path, "w", encoding="utf-8") as f:
                json.dump({"last_low_id": 0}, f, ensure_ascii=False, indent=4)

    def _player_path(self) -> Path:
        return self.base_path / f"0-{self.player_id}.json"

    def _load_raw(self) -> dict:
        path = self._player_path()
        if path.is_file():
            with path.open("r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _save_raw(self, data: dict) -> None:
        path = self._player_path()
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def create_account(self):
        folder_path = self.base_path
        folder_path.mkdir(parents=True, exist_ok=True)

        if not self.metadata_path.exists():
            meta = {"last_low_id": 0}
        else:
            with self.metadata_path.open("r", encoding="utf-8") as f:
                try:
                    meta = json.load(f)
                    if "last_low_id" not in meta:
                        meta["last_low_id"] = 0
                except Exception:
                    meta = {"last_low_id": 0}

        new_low_id = meta["last_low_id"] + 1
        meta["last_low_id"] = new_low_id

        with self.metadata_path.open("w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=4)

        player_filename = folder_path / f"0-{new_low_id}.json"

        # AGGIUNTO: Gems e Coins nel default data
        player_data = {
            "Namecolor": 0,
            "DnDState": 0,
            "TeamChatMuted": 0,
            "ThemeID": 41000005,
            "Region": "OG",  # Default OG non US
            "QuestSeen": False,
            "BattleQuestType": 0,
            "GadgetStatus": True,
            "Name": "Brawler",
            "Registered": False,
            "SupercellIDToken": "",
            "Lang": "EN",
            "Friends": [],
            "Bronze": False,
            "Silver": False,
            "Ruby": False,
            "Rainbow": False,
            "RainbowX": False,
            "Pass": "Password",
            "User": "BSP",
            "Token": "",
            "SelectedStarPowers": {},
            "SelectedGadgets": {},
            "EquippedCards": {},
            "SelectedBrawler": 0,
            "BrawlerTrophies": {},
            "isAndroid": False,
            # NUOVI CAMPI
            "Gems": 0,
            "Coins": 0,
            "TeamID": [0, 0],
            "TeamType": 0,
            "TeamOwnerID": 0,
            "TeamIsOwner": False,
            "TeamMapID": 1,
            # Trophy Road and Brawl Pass. BrawlPassFree and BrawlPassPremium
            # are the tier counters the client renders, TrophyRoadClaimed is
            # the highest tier already handed out.
            "BrawlPassBought": False,
            # freepass and buypass are bitmasks of claimed tiers, not counters.
            # A mask of 0 is what tells the client nothing has been claimed.
            "BrawlPassFree": 0,
            "BrawlPassPremium": 0,
            "BPTOKEN": 0,
            "TrophyRoadClaimed": 0,
            "BrawlerPoints": {},
            "UnlockedBrawlers": {},
            "UnlockedSkins": {}
        }

        with player_filename.open("w", encoding="utf-8") as f:
            json.dump(player_data, f, ensure_ascii=False, indent=4)

        print(f"📂 [DB] Creato file per ID {new_low_id}")
        return str(new_low_id)

    # === METODI ESISTENTI (mantenuti) ===

    def get_scid_token(self) -> str:
        data = self._load_raw()
        return data.get("SupercellIDToken", "")

    def set_scid_token(self, value: str) -> None:
        data = self._load_raw()
        data["SupercellIDToken"] = value if value is not None else ""
        self._save_raw(data)

    @staticmethod
    def get_lowid_by_email(identifier: str, base_dir: str = "data/dynamic") -> Optional[int]:
        if not identifier:
            return None

        pattern = os.path.join(base_dir, "0-*.json")
        for path in glob.glob(pattern):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                continue

            token = data.get("SupercellIDToken", "")
            if token == identifier:
                filename = os.path.basename(path)
                parts = filename.split("-")
                if len(parts) == 2 and parts[1].endswith(".json"):
                    low_str = parts[1].replace(".json", "")
                    try:
                        return int(low_str)
                    except ValueError:
                        continue
        return None

    @staticmethod
    def link_email_to_lowid(identifier: str, low_id: int, base_dir: str = "data/dynamic") -> None:
        if not identifier or not low_id:
            return

        db = DynamicDB(player_id=str(low_id), base_dir=base_dir)
        db.set_scid_token(identifier)
        print(f"[DB] Linkato '{identifier}' all'ID 0-{low_id}")

    @staticmethod
    def clear_scid_everywhere(identifier: str, base_dir: str = "data/dynamic") -> None:
        if not identifier:
            return

        pattern = os.path.join(base_dir, "0-*.json")
        for path in glob.glob(pattern):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                continue

            if data.get("SupercellIDToken", "") == identifier:
                data["SupercellIDToken"] = ""
                try:
                    with open(path, "w", encoding="utf-8") as f:
                        json.dump(data, f, ensure_ascii=False, indent=4)
                    print(f"[DB] Rimossa associazione SCID da {path}")
                except Exception:
                    continue

    def get_name_color(self) -> int:
        data = self._load_raw()
        value = int(data.get("Namecolor", 0))
        return max(0, min(value, 16))

    def set_name_color(self, value: int) -> None:
        value = max(0, min(int(value), 16))
        data = self._load_raw()
        data["Namecolor"] = value
        self._save_raw(data)

    def get_dnd_state(self) -> int:
        data = self._load_raw()
        value = int(data.get("DnDState", 0))
        return 1 if value == 1 else 0

    def set_dnd_state(self, value: int) -> None:
        data = self._load_raw()
        data["DnDState"] = 1 if value == 1 else 0
        self._save_raw(data)

    def get_team_chat_muted(self) -> int:
        data = self._load_raw()
        value = int(data.get("TeamChatMuted", 0))
        return 1 if value == 1 else 0

    def set_team_chat_muted(self, value: int) -> None:
        data = self._load_raw()
        data["TeamChatMuted"] = 1 if value == 1 else 0
        self._save_raw(data)

    def get_theme_id(self) -> int:
        data = self._load_raw()
        return int(data.get("ThemeID", 41000003))

    def set_theme_id(self, value: int) -> None:
        data = self._load_raw()
        data["ThemeID"] = value
        self._save_raw(data)

    def get_region(self) -> str:
        data = self._load_raw()
        return data.get("Region", "OG")  # Default OG

    def set_region(self, region_code: str) -> None:
        data = self._load_raw()
        data["Region"] = str(region_code)
        self._save_raw(data)

    def get_quest_seen(self) -> bool:
        data = self._load_raw()
        return bool(data.get("QuestSeen", False))

    def set_quest_seen(self, value: bool) -> None:
        if not value:
            return

        data = self._load_raw()
        if not data.get("QuestSeen", False):
            data["QuestSeen"] = bool(value)
            self._save_raw(data)

    def get_battle_quest_type(self) -> int:
        data = self._load_raw()
        value = int(data.get("BattleQuestType", 0))
        return 1 if value == 1 else 0

    def set_battle_quest_type(self, value: int) -> None:
        data = self._load_raw()
        data["BattleQuestType"] = 1 if value == 1 else 0
        self._save_raw(data)

    def get_gadget_status(self) -> bool:
        data = self._load_raw()
        return bool(data.get("GadgetStatus", True))

    def set_gadget_status(self, value: bool) -> None:
        data = self._load_raw()
        data["GadgetStatus"] = bool(value)
        self._save_raw(data)

    def get_registered(self) -> bool:
        data = self._load_raw()
        return bool(data.get("Registered", False))

    def set_registered(self, value: bool) -> None:
        data = self._load_raw()
        data["Registered"] = bool(value)
        self._save_raw(data)

    def get_name(self) -> str:
        data = self._load_raw()
        return data.get("Name", "Brawler")

    def set_name(self, name: str) -> None:
        data = self._load_raw()
        data["Name"] = str(name)
        self._save_raw(data)

    def get_friends_list(self) -> list:
        data = self._load_raw()
        return data.get("Friends", [])

    def set_friends_list(self, friends_list: list) -> None:
        data = self._load_raw()
        data["Friends"] = friends_list
        self._save_raw(data)

    def get_player_public_data(self, player_id: int):
        path = f"data/dynamic/0-{player_id}.json"
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data
        return None

    def get_team_membership(self) -> dict:
        data = self._load_raw()
        team_id = data.get("TeamID", [0, 0])
        if not isinstance(team_id, (list, tuple)) or len(team_id) < 2:
            team_id = [0, 0]
        try:
            team_id = [int(team_id[0]), int(team_id[1])]
        except (TypeError, ValueError):
            team_id = [0, 0]
        try:
            team_type = int(data.get("TeamType", 0) or 0)
        except (TypeError, ValueError):
            team_type = 0
        try:
            owner_id = int(data.get("TeamOwnerID", 0) or 0)
        except (TypeError, ValueError):
            owner_id = 0
        try:
            # The old default was index 1 (Wanted3), which is disabled and does
            # not match its own tilemap. Index 4 (Wanted6) is enabled and valid.
            map_id = int(data.get("TeamMapID", 4) or 4)
        except (TypeError, ValueError):
            map_id = 4
        return {
            "TeamID": team_id,
            "TeamType": team_type,
            "TeamOwnerID": owner_id,
            "TeamIsOwner": bool(data.get("TeamIsOwner", False)),
            "TeamMapID": map_id,
        }

    def set_team_membership(
        self,
        team_id: int,
        team_type: int,
        owner_id: int,
        is_owner: bool,
        map_id: int = 1,
        room_high: int = 0,
    ) -> None:
        data = self._load_raw()
        data["TeamID"] = [int(room_high or 0), int(team_id or 0)]
        data["TeamType"] = int(team_type or 0)
        data["TeamOwnerID"] = int(owner_id or 0)
        data["TeamIsOwner"] = bool(is_owner)
        data["TeamMapID"] = int(map_id or 0)
        self._save_raw(data)

    def clear_team_membership(self) -> None:
        data = self._load_raw()
        for key in ("TeamID", "TeamType", "TeamOwnerID", "TeamIsOwner", "TeamMapID"):
            data.pop(key, None)
        self._save_raw(data)

    def get_team_members(self, team_id: int, owner_id: Optional[int] = None) -> list:
        team_id = int(team_id or 0)
        owner_id = int(owner_id or 0) if owner_id is not None else None
        members = []
        if team_id <= 0 or not self.base_path.is_dir():
            return members

        for path in self.base_path.glob("0-*.json"):
            try:
                player_id = int(path.stem.split("-", 1)[1])
                with path.open("r", encoding="utf-8") as file:
                    data = json.load(file)
            except (OSError, ValueError, IndexError, json.JSONDecodeError):
                continue

            stored_team_id = data.get("TeamID", [0, 0])
            if not isinstance(stored_team_id, (list, tuple)) or len(stored_team_id) < 2:
                continue
            try:
                stored_high, stored_low = int(stored_team_id[0]), int(stored_team_id[1])
                stored_owner = int(data.get("TeamOwnerID", 0) or 0)
            except (TypeError, ValueError):
                continue
            if stored_low != team_id:
                continue
            if owner_id is not None and stored_owner not in (0, owner_id) and player_id != owner_id:
                continue

            try:
                stored_type = int(data.get("TeamType", 0) or 0)
                stored_map = int(data.get("TeamMapID", 1) or 0)
            except (TypeError, ValueError):
                stored_type, stored_map = 0, 1
            members.append({
                "player_id": player_id,
                "TeamID": [stored_high, stored_low],
                "TeamType": stored_type,
                "TeamOwnerID": stored_owner,
                "TeamIsOwner": bool(data.get("TeamIsOwner", False)),
                "TeamMapID": stored_map,
                "Name": str(data.get("Name", "Brawler")),
            })

        return sorted(members, key=lambda member: (not member["TeamIsOwner"], member["player_id"]))

    def allocate_team_id(self) -> int:
        self.base_path.mkdir(parents=True, exist_ok=True)
        metadata = {}
        if self.metadata_path.is_file():
            try:
                with self.metadata_path.open("r", encoding="utf-8") as file:
                    metadata = json.load(file)
            except (OSError, json.JSONDecodeError):
                metadata = {}

        highest_stored_id = 0
        for path in self.base_path.glob("0-*.json"):
            try:
                with path.open("r", encoding="utf-8") as file:
                    data = json.load(file)
                team_id = data.get("TeamID", [0, 0])
                if isinstance(team_id, (list, tuple)) and len(team_id) > 1:
                    highest_stored_id = max(highest_stored_id, int(team_id[1] or 0))
            except (OSError, ValueError, TypeError, json.JSONDecodeError):
                continue

        try:
            previous_id = int(metadata.get("last_team_id", 0) or 0)
        except (TypeError, ValueError):
            previous_id = 0
        next_id = max(previous_id, highest_stored_id) + 1
        metadata["last_team_id"] = next_id
        metadata.setdefault("last_low_id", 0)
        with self.metadata_path.open("w", encoding="utf-8") as file:
            json.dump(metadata, file, ensure_ascii=False, indent=4)
        return next_id
    def get_bronze(self) -> bool:
        data = self._load_raw()
        return bool(data.get("Bronze", False))

    def set_bronze(self, value: bool) -> None:
        data = self._load_raw()
        data["Bronze"] = bool(value)
        self._save_raw(data)

    def get_silver(self) -> bool:
        data = self._load_raw()
        return bool(data.get("Silver", False))

    def set_silver(self, value: bool) -> None:
        data = self._load_raw()
        data["Silver"] = bool(value)
        self._save_raw(data)

    def get_ruby(self) -> bool:
        data = self._load_raw()
        return bool(data.get("Ruby", False))

    def set_ruby(self, value: bool) -> None:
        data = self._load_raw()
        data["Ruby"] = bool(value)
        self._save_raw(data)

    def get_rainbow(self) -> bool:
        data = self._load_raw()
        return bool(data.get("Rainbow", False))

    def set_rainbow(self, value: bool) -> None:
        data = self._load_raw()
        data["Rainbow"] = bool(value)
        self._save_raw(data)

    def get_rainbow_x(self) -> bool:
        data = self._load_raw()
        return bool(data.get("RainbowX", False))

    def set_rainbow_x(self, value: bool) -> None:
        data = self._load_raw()
        data["RainbowX"] = bool(value)
        self._save_raw(data)

    def get_can_multi_tier(self) -> bool:
        data = self._load_raw()
        return bool(data.get("CanMultiTier", False))

    def set_can_multi_tier(self, value: bool) -> None:
        data = self._load_raw()
        data["CanMultiTier"] = bool(value)
        self._save_raw(data)

    def get_lang(self) -> str:
        data = self._load_raw()
        return str(data.get("Lang", "EN"))

    def set_lang(self, value: str) -> None:
        data = self._load_raw()
        data["Lang"] = str(value).upper()
        self._save_raw(data)

    def get_pass(self) -> str:
        data = self._load_raw()
        return str(data.get("Pass", "Password"))

    def set_pass(self, value: str) -> None:
        data = self._load_raw()
        data["Pass"] = str(value)
        self._save_raw(data)

    def get_user(self) -> str:
        data = self._load_raw()
        return str(data.get("User", "BSP"))

    def set_user(self, value: str) -> None:
        data = self._load_raw()
        data["User"] = str(value)
        self._save_raw(data)

    def get_token(self) -> str:
        data = self._load_raw()
        return data.get("Token", "")

    def set_token(self, value: str) -> None:
        data = self._load_raw()
        data["Token"] = str(value)
        self._save_raw(data)

    @staticmethod
    def find_lowid_by_token(token: str, base_dir: str = "data/dynamic") -> Optional[int]:
        if not token:
            return None

        pattern = os.path.join(base_dir, "0-*.json")
        for path in glob.glob(pattern):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                continue

            if data.get("Token") == token:
                filename = os.path.basename(path)
                parts = filename.split("-")
                if len(parts) == 2 and parts[1].endswith(".json"):
                    low_str = parts[1].replace(".json", "")
                    try:
                        return int(low_str)
                    except ValueError:
                        continue

        return None

    @staticmethod
    def reassign_token_to_lowid(token: str, new_low_id: int, base_dir: str = "data/dynamic") -> None:
        if not token or new_low_id is None:
            return

        old_low_id = DynamicDB.find_lowid_by_token(token, base_dir=base_dir)

        if old_low_id is not None and old_low_id != new_low_id:
            old_path = os.path.join(base_dir, f"0-{old_low_id}.json")
            try:
                with open(old_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if data.get("Token") == token:
                    data.pop("Token", None)
                    with open(old_path, "w", encoding="utf-8") as f:
                        json.dump(data, f, ensure_ascii=False, indent=4)
                    print(f"[DB] Cleared token from old ID {old_low_id}")
            except Exception:
                pass

        new_db = DynamicDB(player_id=str(new_low_id), base_dir=base_dir)
        new_db.set_token(token)
        print(f"[DB] Assigned token to ID {new_low_id}")

    @staticmethod
    def find_lowid_by_credentials(username: str, password: str, base_dir: str = "data/dynamic") -> Optional[int]:
        if not username or not password:
            return None

        pattern = os.path.join(base_dir, "0-*.json")
        for path in glob.glob(pattern):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                continue

            stored_user = str(data.get("User", ""))
            stored_pass = str(data.get("Pass", ""))

            if stored_user == str(username) and stored_pass == str(password):
                filename = os.path.basename(path)
                parts = filename.split("-")
                if len(parts) == 2 and parts[1].endswith(".json"):
                    low_str = parts[1].replace(".json", "")
                    try:
                        return int(low_str)
                    except ValueError:
                        continue

        return None

    @staticmethod
    def clear_token_everywhere(token: str, base_dir: str = "data/dynamic") -> None:
        if not token:
            return

        pattern = os.path.join(base_dir, "0-*.json")
        for path in glob.glob(pattern):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                continue

            if data.get("Token") == token:
                data.pop("Token", None)
                try:
                    with open(path, "w", encoding="utf-8") as f:
                        json.dump(data, f, ensure_ascii=False, indent=4)
                    print(f"[DB] Cleared token from {path}")
                except Exception:
                    continue

    @staticmethod
    def move_token_to_account(token: str, dest_low_id: int, base_dir: str = "data/dynamic") -> None:
        if not token or dest_low_id is None:
            return

        DynamicDB.clear_token_everywhere(token, base_dir=base_dir)
        dest_db = DynamicDB(player_id=str(dest_low_id), base_dir=base_dir)
        dest_db.set_token(token)
        print(f"[DB] Moved token to 0-{dest_low_id}.json")

    def get_selected_star_powers(self) -> dict:
        data = self._load_raw()
        raw = data.get("SelectedStarPowers", {})
        return {str(k): int(v) for k, v in raw.items()}

    def set_selected_star_powers(self, mapping: dict) -> None:
        data = self._load_raw()
        cleaned = {str(k): int(v) for k, v in mapping.items()}
        data["SelectedStarPowers"] = cleaned
        self._save_raw(data)

    def set_brawler_star_power(self, brawler_id: int, star_power_id: int) -> None:
        data = self._load_raw()
        raw = data.get("SelectedStarPowers", {})
        raw[str(int(brawler_id))] = int(star_power_id)
        data["SelectedStarPowers"] = raw
        self._save_raw(data)

    def get_selected_gadgets(self) -> dict:
        data = self._load_raw()
        raw = data.get("SelectedGadgets", {})
        return {str(k): int(v) for k, v in raw.items()}

    def set_selected_gadgets(self, mapping: dict) -> None:
        data = self._load_raw()
        cleaned = {str(k): int(v) for k, v in mapping.items()}
        data["SelectedGadgets"] = cleaned
        self._save_raw(data)

    def set_brawler_gadget(self, brawler_id: int, gadget_id: int) -> None:
        data = self._load_raw()
        raw = data.get("SelectedGadgets", {})
        raw[str(int(brawler_id))] = int(gadget_id)
        data["SelectedGadgets"] = raw
        self._save_raw(data)

    def get_equipped_star_power(self) -> int:
        return self.SelectedStarPowers.get(str(self.SelectedBrawler), 0)

    def get_equipped_gadget(self) -> int:
        return self.SelectedGadgets.get(str(self.SelectedBrawler), 0)

    def get_equipped_cards(self) -> dict:
        data = self._load_raw()
        raw = data.get("EquippedCards", {})
        try:
            return {int(k): int(v) for k, v in raw.items()}
        except Exception:
            cleaned = {}
            for k, v in raw.items():
                try:
                    cleaned[int(k)] = int(v)
                except Exception:
                    continue
            return cleaned

    def set_equipped_cards(self, mapping: dict) -> None:
        data = self._load_raw()
        cleaned = {str(int(k)): int(v) for k, v in mapping.items()}
        data["EquippedCards"] = cleaned
        self._save_raw(data)

    def set_brawler_equipped_card(self, brawler_id: int, card_id: int) -> None:
        data = self._load_raw()
        raw = data.get("EquippedCards", {})
        raw[str(int(brawler_id))] = int(card_id)
        data["EquippedCards"] = raw
        self._save_raw(data)

    def get_equipped_card_for_brawler(self, brawler_id: int) -> int:
        return self.EquippedCards.get(int(brawler_id), 0)

    def get_selected_brawler(self) -> int:
        data = self._load_raw()
        return int(data.get("SelectedBrawler", 0))

    def set_selected_brawler(self, brawler_id: int) -> None:
        data = self._load_raw()
        data["SelectedBrawler"] = int(brawler_id)
        self._save_raw(data)

    # === METODI PER I TROFEI DEI BRAWLER (NUOVI) ===

    def get_brawler_trophies(self, brawler_id: int) -> int:
        """Ottiene i trofei per un brawler specifico"""
        data = self._load_raw()

        if "BrawlerTrophies" not in data:
            data["BrawlerTrophies"] = {}
            self._save_raw(data)

        key = str(brawler_id)
        if key not in data["BrawlerTrophies"]:
            data["BrawlerTrophies"][key] = 0
            self._save_raw(data)

        return data["BrawlerTrophies"][key]

    def set_brawler_trophies(self, brawler_id: int, trophies: int) -> None:
        """Imposta i trofei per un brawler specifico"""
        data = self._load_raw()

        if "BrawlerTrophies" not in data:
            data["BrawlerTrophies"] = {}

        data["BrawlerTrophies"][str(brawler_id)] = max(0, trophies)
        self._save_raw(data)

    def get_all_brawlers_trophies(self) -> dict:
        """Ottiene i trofei di tutti i brawler come dizionario {brawler_id: trophies}"""
        data = self._load_raw()
        trophies_dict = data.get("BrawlerTrophies", {})
        
        result = {}
        for k, v in trophies_dict.items():
            try:
                result[int(k)] = int(v)
            except (ValueError, TypeError):
                continue
        return result

    def set_all_brawlers_trophies(self, trophies_dict: dict) -> None:
        """Imposta i trofei per tutti i brawler"""
        data = self._load_raw()
        
        cleaned = {}
        for k, v in trophies_dict.items():
            try:
                cleaned[str(int(k))] = max(0, int(v))
            except (ValueError, TypeError):
                continue
        
        data["BrawlerTrophies"] = cleaned
        self._save_raw(data)

    def add_brawler_trophies(self, brawler_id: int, amount: int) -> int:
        """Aggiunge trofei a un brawler (positivo o negativo) e restituisce il nuovo valore"""
        current = self.get_brawler_trophies(brawler_id)
        new_value = max(0, current + amount)
        self.set_brawler_trophies(brawler_id, new_value)
        return new_value

    def get_total_trophies(self) -> int:
        """Ottiene il totale dei trofei di tutti i brawler"""
        all_trophies = self.get_all_brawlers_trophies()
        return sum(all_trophies.values())

    def get_brawler_trophies_sorted(self) -> list:
        """Ottiene i brawler ordinati per trofei (decrescente)"""
        all_trophies = self.get_all_brawlers_trophies()
        sorted_items = sorted(all_trophies.items(), key=lambda x: x[1], reverse=True)
        return [{"brawler_id": brawler_id, "trophies": trophies} for brawler_id, trophies in sorted_items]

    def get_top_brawler(self) -> Optional[int]:
        """Ottiene il brawler con più trofei"""
        all_trophies = self.get_all_brawlers_trophies()
        if not all_trophies:
            return None
        return max(all_trophies.items(), key=lambda x: x[1])[0]

    def get_brawler_rank(self, brawler_id: int) -> int:
        """Ottiene la posizione in classifica di un brawler (1 = primo)"""
        all_trophies = self.get_all_brawlers_trophies()
        sorted_trophies = sorted(all_trophies.values(), reverse=True)
        trophies = self.get_brawler_trophies(brawler_id)
        return sorted_trophies.index(trophies) + 1 if trophies in sorted_trophies else -1

    # === METODI PER ANDROID FLAG ===
    
    def get_is_android(self) -> bool:
        """Ottiene il flag isAndroid dal database"""
        data = self._load_raw()
        return bool(data.get("isAndroid", False))
    
    def set_is_android(self, value: bool) -> None:
        """Imposta il flag isAndroid nel database"""
        data = self._load_raw()
        data["isAndroid"] = bool(value)
        self._save_raw(data)
        print(f"[DB] isAndroid set to {value} for player {self.player_id}")
      
    # === METODI PER LAST ACTIVE ===

    def get_last_active(self) -> int:
        """Ottiene il timestamp dell'ultima attività del giocatore"""
        data = self._load_raw()
        return data.get("LastActive", 0)

    def set_last_active(self, timestamp: int) -> None:
        """Imposta il timestamp dell'ultima attività del giocatore"""
        data = self._load_raw()
        data["LastActive"] = timestamp
        self._save_raw(data)

    def update_last_active(self) -> None:
        """Aggiorna il timestamp dell'ultima attività al momento attuale"""
        import time
        self.set_last_active(int(time.time()))

    def is_online(self, timeout_seconds: int = 300) -> bool:
        """Verifica se il giocatore è online (ultima attività entro timeout_seconds)"""
        import time
        last_active = self.get_last_active()
        if last_active == 0:
            return False
        return (int(time.time()) - last_active) < timeout_seconds

    def get_last_active_str(self) -> str:
        """Restituisce il tempo trascorso dall'ultima attività in formato leggibile"""
        import time
        last_active = self.get_last_active()
        if last_active == 0:
            return "Never"
        
        elapsed = int(time.time()) - last_active
        
        if elapsed < 60:
            return "Online"
        elif elapsed < 3600:
            minutes = elapsed // 60
            return f"{minutes}m ago"
        elif elapsed < 86400:
            hours = elapsed // 3600
            return f"{hours}h ago"
        else:
            days = elapsed // 86400
            return f"{days}d ago"

    # === NUOVI METODI PER GEMS E COINS ===

    def get_gems(self) -> int:
        """Ottiene il numero di Gemme"""
        data = self._load_raw()
        return int(data.get("Gems", 0))

    def set_gems(self, value: int) -> None:
        """Imposta il numero di Gemme"""
        data = self._load_raw()
        data["Gems"] = int(value)
        self._save_raw(data)

    def add_gems(self, amount: int) -> int:
        """Aggiunge (o rimuove) Gemme e restituisce il nuovo totale"""
        current = self.get_gems()
        new_value = current + amount
        # Opzionale: impedire gemme negative? 
        # new_value = max(0, new_value) 
        self.set_gems(new_value)
        return new_value

    def get_coins(self) -> int:
        """Ottiene il numero di Gettoni (Coins)"""
        data = self._load_raw()
        return int(data.get("Coins", 0))

    def set_coins(self, value: int) -> None:
        """Imposta il numero di Gettoni (Coins)"""
        data = self._load_raw()
        data["Coins"] = int(value)
        self._save_raw(data)

    def add_coins(self, amount: int) -> int:
        """Aggiunge (o rimuove) Gettoni e restituisce il nuovo totale"""
        current = self.get_coins()
        new_value = current + amount
        new_value = max(0, new_value) # Impedisce coins negativi
        self.set_coins(new_value)
        return new_value

    @staticmethod
    def _int_map(data, key):
        """Read a per id map, dropping anything that is not an int pair."""
        raw = data.get(key, {})
        if not isinstance(raw, dict):
            return {}
        result = {}
        for name, value in raw.items():
            try:
                result[str(int(name))] = int(value)
            except (TypeError, ValueError):
                continue
        return result

    # === TROPHY ROAD E BRAWL PASS ===

    def get_brawl_pass_bought(self) -> bool:
        data = self._load_raw()
        return bool(data.get("BrawlPassBought", False))

    def set_brawl_pass_bought(self, value: bool) -> None:
        data = self._load_raw()
        data["BrawlPassBought"] = bool(value)
        self._save_raw(data)

    def get_brawl_pass_tokens(self) -> int:
        """Pro tokens collected, which is what the tier threshold reads."""
        data = self._load_raw()
        return int(data.get("BPTOKEN", 0) or 0)

    def add_brawl_pass_tokens(self, amount: int) -> int:
        data = self._load_raw()
        current = int(data.get("BPTOKEN", 0) or 0)
        data["BPTOKEN"] = max(0, current + int(amount))
        self._save_raw(data)
        return data["BPTOKEN"]

    def set_brawl_pass_tokens(self, value: int) -> int:
        data = self._load_raw()
        data["BPTOKEN"] = max(0, int(value))
        self._save_raw(data)
        return data["BPTOKEN"]

    # === TOKEN MULTIPLIER (TokensDoubler) ===
    def get_tokens_doubler(self) -> int:
        """Ottiene il moltiplicatore token (TokensDoubler)"""
        data = self._load_raw()
        return int(data.get("TokensDoubler", 0))

    def set_tokens_doubler(self, value: int) -> None:
        """Imposta il moltiplicatore token"""
        data = self._load_raw()
        data["TokensDoubler"] = max(0, int(value))
        self._save_raw(data)

    def add_tokens_doubler(self, amount: int) -> int:
        """Aggiunge/rimuove dal moltiplicatore token"""
        current = self.get_tokens_doubler()
        new_value = max(0, current + amount)
        self.set_tokens_doubler(new_value)
        return new_value

    # === STAR POINTS ===
    def get_star_points(self) -> int:
        """Ottiene gli Star Points"""
        data = self._load_raw()
        return int(data.get("StarPoints", 0))

    def set_star_points(self, value: int) -> None:
        """Imposta gli Star Points"""
        data = self._load_raw()
        data["StarPoints"] = max(0, int(value))
        self._save_raw(data)

    def add_star_points(self, amount: int) -> int:
        """Aggiunge/rimuove Star Points"""
        current = self.get_star_points()
        new_value = max(0, current + amount)
        self.set_star_points(new_value)
        return new_value

    # === TROPHIES (totali) ===
    def add_total_trophies(self, amount: int) -> int:
        """Aggiunge/rimuove trofei totali (distribuisce sul brawler selezionato)"""
        # Per semplicità, aggiunge al brawler selezionato
        selected = self.get_selected_brawler()
        current = self.get_brawler_trophies(selected)
        new_value = max(0, current + amount)
        self.set_brawler_trophies(selected, new_value)
        return new_value

    def get_brawl_pass_claimed(self, premium: bool, season: int = 0) -> int:
        """The claimed tier bitmask.

        The v29 client carries this as a mask, not a counter: claiming tier i
        sets bit i plus 2, so a mask of 0 means nothing has been claimed. It is
        written with writeInt rather than writeVInt because of that.

        Season-aware: each season has its own bitmask.
        """
        data = self._load_raw()
        key = ("BrawlPassPremium" if premium else "BrawlPassFree") + f"_S{season}"
        return int(data.get(key, 0) or 0)

    def set_brawl_pass_claimed(self, premium: bool, mask: int, season: int = 0) -> None:
        data = self._load_raw()
        key = ("BrawlPassPremium" if premium else "BrawlPassFree") + f"_S{season}"
        data[key] = int(mask)
        self._save_raw(data)

    def claim_brawl_pass_tier(self, premium: bool, tier: int, season: int = 0) -> bool:
        """Set the bit for a tier. False when it was already claimed.
        
        v29 client uses bit i+2 for tier i (tier 0 = bit 2, tier 1 = bit 3, etc.)
        """
        mask = self.get_brawl_pass_claimed(premium, season)
        bit = 4 * (1 << int(tier))  # 1 << (tier + 2)
        if mask & bit:
            return False
        self.set_brawl_pass_claimed(premium, mask | bit, season)
        return True

    def brawl_pass_tier_count(self, premium: bool, season: int = 0) -> int:
        """How many tiers the mask has claimed, so a count can be reported."""
        mask = self.get_brawl_pass_claimed(premium, season)
        return bin(mask >> 2).count("1")

    def get_brawl_pass_claimed_split(self, premium: bool, season: int = 0) -> list:
        """
        Get the claimed bitmask split into 4 ints (32 bits each) for the client.
        The client expects 4 separate ints for premium and 4 for free tiers.
        """
        mask = self.get_brawl_pass_claimed(premium, season)
        # Split 128-bit mask into 4 x 32-bit ints (little-endian order)
        return [
            mask & 0xFFFFFFFF,
            (mask >> 32) & 0xFFFFFFFF,
            (mask >> 64) & 0xFFFFFFFF,
            (mask >> 96) & 0xFFFFFFFF,
        ]

    def set_brawl_pass_claimed_from_split(self, premium: bool, parts: list, season: int = 0) -> None:
        """Set the claimed bitmask from 4 split ints."""
        mask = (parts[0] & 0xFFFFFFFF) | \
               ((parts[1] & 0xFFFFFFFF) << 32) | \
               ((parts[2] & 0xFFFFFFFF) << 64) | \
               ((parts[3] & 0xFFFFFFFF) << 96)
        self.set_brawl_pass_claimed(premium, mask, season)

    def get_trophy_road_claimed(self, season: int = 0) -> int:
        data = self._load_raw()
        key = f"TrophyRoadClaimed_S{season}"
        return int(data.get(key, 0) or 0)

    def set_trophy_road_claimed(self, tier: int, season: int = 0) -> None:
        """Only ever moves forward, so a replayed claim cannot lower it."""
        data = self._load_raw()
        key = f"TrophyRoadClaimed_S{season}"
        current = int(data.get(key, 0) or 0)
        data[key] = max(current, int(tier))
        self._save_raw(data)

    def get_brawler_points(self) -> dict:
        return DynamicDB._int_map(self._load_raw(), "BrawlerPoints")

    def add_brawler_points(self, brawler_id: int, amount: int) -> int:
        data = self._load_raw()
        points = DynamicDB._int_map(data, "BrawlerPoints")
        key = str(int(brawler_id))
        points[key] = max(0, points.get(key, 0) + int(amount))
        data["BrawlerPoints"] = points
        self._save_raw(data)
        return points[key]

    def set_brawler_unlocked(self, brawler_id: int, unlocked: bool = True) -> None:
        data = self._load_raw()
        unlocked_map = DynamicDB._int_map(data, "UnlockedBrawlers")
        unlocked_map[str(int(brawler_id))] = 1 if unlocked else 0
        data["UnlockedBrawlers"] = unlocked_map
        self._save_raw(data)

    def set_skin_unlocked(self, skin_id: int, unlocked: bool = True) -> None:
        data = self._load_raw()
        unlocked_map = DynamicDB._int_map(data, "UnlockedSkins")
        unlocked_map[str(int(skin_id))] = 1 if unlocked else 0
        data["UnlockedSkins"] = unlocked_map
        self._save_raw(data)

    # === METODI STATICI PER OPERAZIONI GLOBALI ===

    @staticmethod
    def get_brawler_trophies_from_db(player_id: int, brawler_id: int, base_dir: str = "data/dynamic") -> int:
        """Metodo statico per ottenere i trofei di un brawler da un player_id"""
        db = DynamicDB(player_id=str(player_id), base_dir=base_dir)
        return db.get_brawler_trophies(brawler_id)

    @staticmethod
    def set_brawler_trophies_for_player(player_id: int, brawler_id: int, trophies: int, base_dir: str = "data/dynamic") -> None:
        """Metodo statico per impostare i trofei di un brawler per un player"""
        db = DynamicDB(player_id=str(player_id), base_dir=base_dir)
        db.set_brawler_trophies(brawler_id, trophies)
