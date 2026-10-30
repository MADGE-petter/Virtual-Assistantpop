"""Collection Service - Business logic for eggs, gacha, shop, shards, coins and equip."""

import threading
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Callable, Dict, List, Optional

from database.collection_repository import CollectionRepository
from service.collection.character_registry import (
    DEFAULT_CHARACTER_ID,
    RARITY_INFO,
    CharacterDef,
    CharacterRegistry,
)
from service.collection.gacha_engine import PITY_THRESHOLD, GachaEngine

# ---------------- Economy constants ----------------
EGG_PRICE = 200
ROLL_SINGLE_COST = 200
ROLL_FIVE_COST = 1000
DAILY_COINS = 50
VOICE_COINS_PER_COMMAND = 5
VOICE_COINS_DAILY_CAP = 100
STREAK_EGG_EVERY = 7


@dataclass
class OpenResult:
    character: CharacterDef
    is_new: bool
    shards_gained: int
    pity_after: int
    is_bonus: bool = False


@dataclass
class ActionOutcome:
    ok: bool
    message: str


class CollectionService:
    """One instance per logged-in user (see get_collection_service)."""

    def __init__(self, user_key: str, repo: Optional[CollectionRepository] = None,
                 engine: Optional[GachaEngine] = None):
        self.user_key = user_key or "guest"
        self.repo = repo or CollectionRepository()
        self.engine = engine or GachaEngine()
        self.registry = CharacterRegistry.instance()
        self._lock = threading.RLock()
        self._equip_listeners: List[Callable[[CharacterDef], None]] = []
        self._ensure_starter()

    # ============================================================
    # LISTENERS
    # ============================================================
    def on_equip_changed(self, callback: Callable[[CharacterDef], None]) -> None:
        self._equip_listeners.append(callback)

    def _emit_equip(self, char: CharacterDef) -> None:
        for cb in list(self._equip_listeners):
            try:
                cb(char)
            except Exception as e:
                print(f"[CollectionService] equip listener error: {e}")

    # ============================================================
    # STATE
    # ============================================================
    @property
    def is_admin(self) -> bool:
        return self.user_key.strip().lower() == "admin"

    def wallet(self) -> Dict:
        w = self.repo.get_wallet(self.user_key)
        if self.is_admin:
            # Đặc quyền admin tối cao: vô hạn xu, mảnh vỡ và trứng
            w["coins"] = 999999999
            w["shards"] = 999999999
            w["eggs"] = 999999
            w["streak"] = 999
        return w

    def owned(self) -> Dict[str, int]:
        if self.is_admin:
            # Sở hữu full toàn bộ linh vật trong game
            return {c.id: 99 for c in self.registry.all()}
        return self.repo.get_owned(self.user_key)

    def equipped(self) -> CharacterDef:
        cid = self.wallet().get("equipped") or DEFAULT_CHARACTER_ID
        char = self.registry.get(cid)
        if char is None or cid not in self.owned():
            char = self.registry.get(DEFAULT_CHARACTER_ID)
        assert char is not None
        return char

    def pity_remaining(self) -> int:
        return max(0, PITY_THRESHOLD - int(self.wallet()["pity"]))

    def _ensure_starter(self) -> None:
        with self._lock:
            w = self.wallet()
            if self.is_admin:
                for c in self.registry.all():
                    if c.id not in self.repo.get_owned(self.user_key):
                        self.repo.add_owned(self.user_key, c.id)
                self.repo.update_wallet(self.user_key, coins=999999999, shards=999999999, eggs=999999)
                return

            if DEFAULT_CHARACTER_ID not in self.owned():
                self.repo.add_owned(self.user_key, DEFAULT_CHARACTER_ID)
            if not w["starter_given"]:
                self.repo.update_wallet(self.user_key, eggs=w["eggs"] + 1, starter_given=1)
                self.repo.log(self.user_key, "starter_egg", "egg", 1)

    # ============================================================
    # EARNING
    # ============================================================
    def claim_daily(self) -> Optional[str]:
        """Claim daily login reward. Returns a message if something was granted."""
        with self._lock:
            w = self.wallet()
            today = date.today()
            if w["last_daily"] == today.isoformat():
                return None
            yesterday = (today - timedelta(days=1)).isoformat()
            streak = w["streak"] + 1 if w["last_daily"] == yesterday else 1
            eggs = w["eggs"]
            msg = f"Điểm danh ngày {streak}: +{DAILY_COINS} Pop Coin"
            if streak % STREAK_EGG_EVERY == 0:
                eggs += 1
                msg += " và 1 trứng thưởng chuỗi 7 ngày!"
                self.repo.log(self.user_key, "streak_egg", "egg", 1)
            self.repo.update_wallet(self.user_key, coins=w["coins"] + DAILY_COINS,
                                    last_daily=today.isoformat(), streak=streak, eggs=eggs)
            self.repo.log(self.user_key, "daily", "coin", DAILY_COINS)
            return msg

    def reward_voice_command(self) -> int:
        """Grant coins for using the assistant. Returns coins granted (0 if capped)."""
        with self._lock:
            w = self.wallet()
            today = date.today().isoformat()
            earned_today = w["voice_coins_today"] if w["voice_day"] == today else 0
            grant = min(VOICE_COINS_PER_COMMAND, VOICE_COINS_DAILY_CAP - earned_today)
            if grant <= 0:
                return 0
            self.repo.update_wallet(self.user_key, coins=w["coins"] + grant,
                                    voice_day=today, voice_coins_today=earned_today + grant)
            self.repo.log(self.user_key, "voice", "coin", grant)
            return grant

    def add_coins(self, amount: int) -> int:
        """Add coins (useful for testing or rewards)."""
        with self._lock:
            w = self.wallet()
            new_amount = max(0, w["coins"] + amount)
            self.repo.update_wallet(self.user_key, coins=new_amount)
            self.repo.log(self.user_key, "add_coins", "coin", amount)
            return new_amount

    def add_shards(self, amount: int) -> int:
        """Add shards (useful for testing or rewards)."""
        with self._lock:
            w = self.wallet()
            new_amount = max(0, w["shards"] + amount)
            self.repo.update_wallet(self.user_key, shards=new_amount)
            self.repo.log(self.user_key, "add_shards", "shard", amount)
            return new_amount

    # ============================================================
    # SPENDING
    # ============================================================
    def buy_egg(self, qty: int = 1) -> ActionOutcome:
        with self._lock:
            if self.is_admin:
                return ActionOutcome(True, f"[Admin] Đã cấp {qty} trứng gacha vô hạn.")
            w = self.wallet()
            cost = EGG_PRICE * qty
            if w["coins"] < cost:
                return ActionOutcome(False, f"Không đủ Pop Coin (cần {cost}).")
            self.repo.update_wallet(self.user_key, coins=w["coins"] - cost, eggs=w["eggs"] + qty)
            self.repo.log(self.user_key, "buy_egg", "coin", -cost)
            return ActionOutcome(True, f"Đã mua {qty} trứng.")

    def open_egg(self, featured_id: Optional[str] = None) -> Optional[OpenResult]:
        with self._lock:
            w = self.wallet()
            use_coin = False
            if not self.is_admin:
                if w["eggs"] <= 0:
                    if w["coins"] < ROLL_SINGLE_COST:
                        return None
                    use_coin = True
            char, new_pity = self.engine.roll(
                self.registry.gacha_pool(),
                int(w["pity"]),
                featured_id=featured_id,
            )
            is_new = (char.id not in self.repo.get_owned(self.user_key)) if self.is_admin else (char.id not in self.owned())
            self.repo.add_owned(self.user_key, char.id)
            shards = 0 if is_new else RARITY_INFO[char.rarity]["shard_gain"]
            if not self.is_admin:
                if use_coin:
                    self.repo.update_wallet(
                        self.user_key,
                        coins=w["coins"] - ROLL_SINGLE_COST,
                        pity=new_pity,
                        shards=w["shards"] + shards,
                        total_opened=w["total_opened"] + 1,
                    )
                    self.repo.log(self.user_key, "roll_coin", "coin", -ROLL_SINGLE_COST, char.id)
                else:
                    self.repo.update_wallet(
                        self.user_key,
                        eggs=w["eggs"] - 1,
                        pity=new_pity,
                        shards=w["shards"] + shards,
                        total_opened=w["total_opened"] + 1,
                    )
                    self.repo.log(self.user_key, "open_egg", "egg", -1, char.id)
            if shards:
                self.repo.log(self.user_key, "duplicate", "shard", shards, char.id)
            return OpenResult(char, is_new, shards, new_pity, is_bonus=False)

    def roll_with_coins(
        self,
        count: int = 1,
        featured_id: Optional[str] = None,
    ) -> tuple[ActionOutcome, List[OpenResult]]:
        """
        Direct coin gacha roll:
        - count == 1: 200 Xu -> 1 roll.
        - count == 5: 1,000 Xu -> 5 rolls + 1 Bonus Random Rate roll (min_rarity='rare').
        """
        with self._lock:
            w = self.wallet()
            cost = ROLL_FIVE_COST if count >= 5 else (ROLL_SINGLE_COST * count)
            if not self.is_admin and int(w["coins"]) < cost:
                needed = cost - int(w["coins"])
                return (
                    ActionOutcome(False, f"Bạn còn thiếu {needed:,} Xu (Cần {cost:,} Xu, hiện có {int(w['coins']):,} Xu)."),
                    [],
                )

            pool = self.registry.gacha_pool()
            pity = int(w["pity"])
            shards_total = int(w["shards"])
            total_opened = int(w["total_opened"])
            owned_set = set(self.repo.get_owned(self.user_key).keys())

            results: List[OpenResult] = []
            for _ in range(count):
                char, pity = self.engine.roll(pool, pity, featured_id=featured_id)
                is_new = char.id not in owned_set
                owned_set.add(char.id)
                self.repo.add_owned(self.user_key, char.id)
                shards = 0 if is_new else RARITY_INFO[char.rarity]["shard_gain"]
                shards_total += shards
                total_opened += 1
                results.append(OpenResult(char, is_new, shards, pity, is_bonus=False))

            # Nếu quay gói 5 lần (1,000 Xu): Tặng thêm +1 lượt Rate ngẫu nhiên (tối thiểu Hiếm+)
            if count >= 5:
                bonus_char, pity = self.engine.roll(
                    pool,
                    pity,
                    featured_id=featured_id,
                    min_rarity="rare",
                )
                is_new_b = bonus_char.id not in owned_set
                owned_set.add(bonus_char.id)
                self.repo.add_owned(self.user_key, bonus_char.id)
                shards_b = 0 if is_new_b else RARITY_INFO[bonus_char.rarity]["shard_gain"]
                shards_total += shards_b
                total_opened += 1
                results.append(OpenResult(bonus_char, is_new_b, shards_b, pity, is_bonus=True))

            if not self.is_admin:
                self.repo.update_wallet(
                    self.user_key,
                    coins=int(w["coins"]) - cost,
                    pity=pity,
                    shards=shards_total,
                    total_opened=total_opened,
                )
                self.repo.log(self.user_key, f"roll_x{count}", "coin", -cost)

            return ActionOutcome(True, "Triệu hồi thành công!"), results

    def buy_character(self, char_id: str) -> ActionOutcome:
        with self._lock:
            char = self.registry.get(char_id)
            if char is None:
                return ActionOutcome(False, "Nhân vật không tồn tại.")
            if self.is_admin:
                return ActionOutcome(True, f"[Admin] Đã kích hoạt toàn quyền {char.name}!")
            if char_id in self.owned():
                return ActionOutcome(False, "Bạn đã sở hữu nhân vật này.")
            w = self.wallet()
            if w["coins"] < char.price:
                return ActionOutcome(False, f"Không đủ Pop Coin (cần {char.price:,}).")
            self.repo.update_wallet(self.user_key, coins=w["coins"] - char.price)
            self.repo.add_owned(self.user_key, char_id)
            self.repo.log(self.user_key, "buy_character", "coin", -char.price, char_id)
            return ActionOutcome(True, f"Đã sở hữu {char.name}!")

    def exchange_shards(self, char_id: str) -> ActionOutcome:
        with self._lock:
            char = self.registry.get(char_id)
            if char is None:
                return ActionOutcome(False, "Nhân vật không tồn tại.")
            if self.is_admin:
                return ActionOutcome(True, f"[Admin] Đã kích hoạt toàn quyền {char.name}!")
            if char_id in self.owned():
                return ActionOutcome(False, "Bạn đã sở hữu nhân vật này.")
            cost = RARITY_INFO[char.rarity]["shard_cost"]
            w = self.wallet()
            if w["shards"] < cost:
                return ActionOutcome(False, f"Không đủ Mảnh (cần {cost}).")
            self.repo.update_wallet(self.user_key, shards=w["shards"] - cost)
            self.repo.add_owned(self.user_key, char_id)
            self.repo.log(self.user_key, "exchange_shards", "shard", -cost, char_id)
            return ActionOutcome(True, f"Đã đổi Mảnh lấy {char.name}!")

    def equip(self, char_id: str) -> ActionOutcome:
        with self._lock:
            char = self.registry.get(char_id)
            if char is None:
                return ActionOutcome(False, "Nhân vật không tồn tại.")
            if not self.is_admin and char_id not in self.owned():
                return ActionOutcome(False, "Bạn chưa sở hữu nhân vật này.")
            self.repo.update_wallet(self.user_key, equipped=char_id)
        self._emit_equip(char)
        prefix = "[Admin] " if self.is_admin else ""
        return ActionOutcome(True, f"{prefix}Đã trang bị {char.name}.")

    # Aliases for shop/UI compatibility
    buy_character_with_coins = buy_character
    exchange_character_with_shards = exchange_shards


# ============================================================
# PER-USER SINGLETON ACCESS
# ============================================================
_services: Dict[str, CollectionService] = {}
_current_user: str = "guest"
_services_lock = threading.Lock()


def get_collection_service(user_key: Optional[str] = None) -> CollectionService:
    global _current_user
    with _services_lock:
        key = user_key or _current_user or "guest"
        if user_key:
            _current_user = user_key
        if key not in _services:
            _services[key] = CollectionService(key)
        return _services[key]
