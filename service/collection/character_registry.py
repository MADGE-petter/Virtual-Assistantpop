"""Character Registry - Catalog of collectible mascot characters.

Holds rarity configuration, built-in vector characters and PNG skin packs
scanned from `skins/<id>/manifest.json`.
"""

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from utils.paths import get_writeable_path, resource_path

# ============================================================
# RARITY CONFIGURATION
# ============================================================

RARITY_ORDER = ["common", "rare", "epic", "legendary", "mythic"]

RARITY_INFO: Dict[str, Dict[str, Any]] = {
    "common":    {"label": "Thường",      "color": "#94A3B8", "glow": "#CBD5E1", "rate": 0.60, "price": 500,   "shard_gain": 10,  "shard_cost": 50},
    "rare":      {"label": "Hiếm",        "color": "#38BDF8", "glow": "#7DD3FC", "rate": 0.25, "price": 1500,  "shard_gain": 25,  "shard_cost": 120},
    "epic":      {"label": "Sử thi",      "color": "#A855F7", "glow": "#D8B4FE", "rate": 0.10, "price": 4000,  "shard_gain": 60,  "shard_cost": 300},
    "legendary": {"label": "Huyền thoại", "color": "#F59E0B", "glow": "#FCD34D", "rate": 0.04, "price": 10000, "shard_gain": 150, "shard_cost": 800},
    "mythic":    {"label": "Thần thoại",  "color": "#F43F5E", "glow": "#FDA4AF", "rate": 0.01, "price": 20000, "shard_gain": 400, "shard_cost": 2000},
}

DEFAULT_CHARACTER_ID = "pop"


def rarity_rank(rarity: str) -> int:
    return RARITY_ORDER.index(rarity) if rarity in RARITY_ORDER else 0


@dataclass
class CharacterDef:
    id: str
    name: str
    rarity: str
    description: str
    kind: str = "vector"            # "pop" | "vector" | "png"
    spec: Dict[str, Any] = field(default_factory=dict)
    skin_dir: Optional[str] = None
    price_override: Optional[int] = None
    in_gacha: bool = True

    @property
    def price(self) -> int:
        if self.price_override is not None:
            return self.price_override
        return RARITY_INFO[self.rarity]["price"]

    @property
    def rarity_label(self) -> str:
        return RARITY_INFO[self.rarity]["label"]

    @property
    def rarity_color(self) -> str:
        return RARITY_INFO[self.rarity]["color"]


# ============================================================
# BUILT-IN ORIGINAL CHARACTERS (vector rendered)
# ============================================================

_BUILTINS: List[CharacterDef] = [
    CharacterDef(
        id="pop", name="Pop", rarity="common", kind="pop", in_gacha=False, price_override=0,
        description="Mèo cyber nguyên bản, người bạn đầu tiên của bạn.",
    ),
    # ---------------- Common ----------------
    CharacterDef(
        id="neon_cat", name="Mèo Neon", rarity="common",
        description="Chú mèo phát sáng hồng neon, thích ngủ trên bàn phím.",
        spec={"shape": "round", "body": "#2A1B3D", "body2": "#1A1028", "accent": "#FF4FD8",
              "eye": "#FF4FD8", "ears": "cat", "tail": "cat", "extras": ["whiskers"]},
    ),
    CharacterDef(
        id="bun_bao", name="Bánh Bao Tròn Ủm", rarity="common",
        description="Cục bánh bao trắng mềm, bị chọc là phồng má.",
        spec={"shape": "blob", "body": "#FFF4E6", "body2": "#F3DCC0", "accent": "#F59E0B",
              "eye": "#3B2A1A", "ears": "none", "tail": "none", "extras": ["bun_swirl", "big_blush"],
              "outline": "#D9B48A", "light_body": True},
    ),
    CharacterDef(
        id="pixel_chick", name="Gà Con Pixel", rarity="common",
        description="Gà con 8-bit, kêu 'píp' mỗi lần bạn ra lệnh.",
        spec={"shape": "square", "body": "#FACC15", "body2": "#EAB308", "accent": "#F97316",
              "eye": "#1F2937", "ears": "none", "tail": "none", "extras": ["comb", "beak", "pixel_grid"],
              "outline": "#B45309", "light_body": True},
    ),
    # ---------------- Rare ----------------
    CharacterDef(
        id="snow_fox", name="Cáo Tuyết", rarity="rare",
        description="Cáo trắng vùng băng giá, đuôi bông xù toả hơi lạnh.",
        spec={"shape": "round", "body": "#E8F4FF", "body2": "#C7E2F7", "accent": "#38BDF8",
              "eye": "#0EA5E9", "ears": "fox", "tail": "fox", "extras": ["snowflake"],
              "outline": "#7FB5DB", "light_body": True},
    ),
    CharacterDef(
        id="robo_mini", name="Robo Mini", rarity="rare",
        description="Robot tí hon có ăng-ten, mắt là màn hình LED.",
        spec={"shape": "square", "body": "#475569", "body2": "#334155", "accent": "#22D3EE",
              "eye": "#22D3EE", "ears": "bolts", "tail": "none", "extras": ["antenna", "led_eyes"]},
    ),
    CharacterDef(
        id="jelly_slime", name="Slime Thạch", rarity="rare",
        description="Slime thạch xanh trong veo, lắc lư dẻo quẹo.",
        spec={"shape": "slime", "body": "#4ADE80", "body2": "#16A34A", "accent": "#BBF7D0",
              "eye": "#052E16", "ears": "none", "tail": "none", "extras": ["drip", "shine"],
              "alpha": 210, "light_body": True},
    ),
    # ---------------- Epic ----------------
    CharacterDef(
        id="ice_princess", name="Công Chúa Băng Kem", rarity="epic",
        description="Công chúa xứ kem tuyết, vương miện pha lê và áo choàng băng giá.",
        spec={"shape": "round", "body": "#DBEAFE", "body2": "#93C5FD", "accent": "#60A5FA",
              "eye": "#2563EB", "ears": "none", "tail": "none",
              "extras": ["ice_crown", "hair_buns", "cape", "sparkles"],
              "outline": "#3B82F6", "light_body": True},
    ),
    CharacterDef(
        id="transform_warrior", name="Chiến Binh Biến Hình", rarity="epic",
        description="Chiến binh cơ giáp biến thành xe đua khi bạn gọi.",
        spec={"shape": "square", "body": "#B91C1C", "body2": "#7F1D1D", "accent": "#FBBF24",
              "eye": "#38BDF8", "ears": "fins", "tail": "none",
              "extras": ["visor", "chest_plate", "wheels", "transform_morph"]},
    ),
    # ---------------- Legendary ----------------
    CharacterDef(
        id="star_dragon", name="Rồng Sao", rarity="legendary",
        description="Rồng con sinh ra từ dải ngân hà, vảy lấp lánh như sao.",
        spec={"shape": "round", "body": "#1E1B4B", "body2": "#0F0A2E", "accent": "#818CF8",
              "eye": "#FCD34D", "ears": "horns", "tail": "dragon",
              "extras": ["dragon_wings", "star_scales", "orbit_stars"]},
    ),
    # ---------------- Mythic ----------------
    CharacterDef(
        id="cosmic_phoenix", name="Phượng Hoàng Vũ Trụ", rarity="mythic",
        description="Phượng hoàng tái sinh từ tinh vân, cánh lửa đổi màu cầu vồng.",
        spec={"shape": "round", "body": "#7C2D12", "body2": "#431407", "accent": "#FB923C",
              "eye": "#FDE047", "ears": "crest", "tail": "phoenix",
              "extras": ["flame_wings", "halo", "rainbow_aura", "orbit_stars"]},
    ),
    CharacterDef(
        id="white_fox_girl", name="Hồ Ly Bạch Tâm", rarity="mythic", kind="fox_girl",
        description="Thiếu nữ thú nhân cáo trắng đáng yêu mặc áo len trắng dài họa tiết trái tim. Khi ngủ sẽ hóa thành cáo bông cuộn tròn hoặc ngủ gật phồng bong bóng mũi.",
    ),
    CharacterDef(
        id="phoebe_chuby", name="Phoebe Chupi", rarity="mythic", kind="phoebe_chuby",
        description="Meme Phoebe Chupi tròn ủm siêu đáng yêu với đôi má bánh bao phúng phính, bím tóc nơ xanh-trắng và tiếng kêu 'Chupi~!' chữa lành vô tận.",
    ),
    CharacterDef(
        id="nono_chubby", name="Nono (Phruonuo)", rarity="mythic", kind="nono_chubby",
        description="Bé Nono bánh bao núng nính (Phrolova Chubby) với tóc xám bạc buộc hai bên, hoa bỉ ngạn đỏ và băng bịt mắt trắng, biểu cảm ngơ ngác siêu cưng.",
    ),
]


class CharacterRegistry:
    """Loads and indexes all collectible characters (built-in + PNG skins)."""

    _instance: Optional["CharacterRegistry"] = None

    def __init__(self):
        self._chars: Dict[str, CharacterDef] = {}
        self.reload()

    @classmethod
    def instance(cls) -> "CharacterRegistry":
        if cls._instance is None:
            cls._instance = CharacterRegistry()
        return cls._instance

    # --------------------------------------------------------
    def reload(self):
        self._chars = {c.id: c for c in _BUILTINS}
        for skin in self._scan_skin_packs():
            if skin.id in self._chars:
                print(f"[CharacterRegistry] Skin id '{skin.id}' trùng nhân vật có sẵn, bỏ qua.")
                continue
            self._chars[skin.id] = skin

    @staticmethod
    def skin_dirs() -> List[str]:
        dirs = []
        bundled = resource_path("skins")
        writable = os.path.dirname(get_writeable_path("skins", "_"))
        for d in (bundled, writable):
            if d not in dirs:
                dirs.append(d)
        return dirs

    def _scan_skin_packs(self) -> List[CharacterDef]:
        found: List[CharacterDef] = []
        for base in self.skin_dirs():
            if not os.path.isdir(base):
                continue
            for name in sorted(os.listdir(base)):
                folder = os.path.join(base, name)
                manifest = os.path.join(folder, "manifest.json")
                if not os.path.isfile(manifest):
                    continue
                try:
                    with open(manifest, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    if not os.path.isfile(os.path.join(folder, "idle.png")):
                        print(f"[CharacterRegistry] Skin '{name}' thiếu idle.png, bỏ qua.")
                        continue
                    rarity = str(data.get("rarity", "common")).lower()
                    if rarity not in RARITY_INFO:
                        rarity = "common"
                    price = data.get("price")
                    found.append(CharacterDef(
                        id=str(data.get("id") or name),
                        name=str(data.get("name") or name),
                        rarity=rarity,
                        description=str(data.get("description", "")),
                        kind="png",
                        skin_dir=folder,
                        price_override=int(price) if isinstance(price, (int, float)) else None,
                        in_gacha=bool(data.get("in_gacha", True)),
                    ))
                except Exception as e:
                    print(f"[CharacterRegistry] Lỗi đọc skin '{name}': {e}")
        return found

    # --------------------------------------------------------
    def get(self, char_id: str) -> Optional[CharacterDef]:
        return self._chars.get(char_id)

    def all(self) -> List[CharacterDef]:
        return sorted(self._chars.values(), key=lambda c: (rarity_rank(c.rarity), c.name))

    def gacha_pool(self) -> List[CharacterDef]:
        return [c for c in self._chars.values() if c.in_gacha]

    def shop_items(self) -> List[CharacterDef]:
        return [c for c in self.all() if c.id != DEFAULT_CHARACTER_ID]
