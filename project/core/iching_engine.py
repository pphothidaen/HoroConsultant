"""
I Ching & Liu Yao (易經 & 六爻) Core Calculation Engine
======================================================
Deterministic calculation of I Ching 64 Hexagrams & Liu Yao divinations:
- Hexagram casting (Yarrow / Coin toss / Number / Time)
- 64 Hexagrams lookup & Trigrams (八卦)
- Na Jia Stems & Branches mapping (納甲地支)
- Five Relatives (五親: 父母, 兄弟, 子孫, 妻財, 官鬼)
- Six Animals / Spirits (六神: 青龍, 朱雀, 勾陳, 騰蛇, 白虎, 玄武)
"""

from __future__ import annotations

import random
from typing import Any

from project.core.base_engine import AbstractAstrologyEngine, EngineChartResult

TRIGRAM_NAMES = ["坤", "震", "坎", "兌", "艮", "離", "巽", "乾"]
TRIGRAM_BINARY = {
    "000": "坤", "100": "震", "010": "坎", "110": "兌",
    "001": "艮", "101": "離", "011": "巽", "111": "乾",
}
TRIGRAM_INFO = {
    "坤": {"binary": "000", "symbol": "☷", "nature": "地 (Earth)", "element": "土"},
    "震": {"binary": "100", "symbol": "☳", "nature": "雷 (Thunder)", "element": "木"},
    "坎": {"binary": "010", "symbol": "☵", "nature": "水 (Water)", "element": "水"},
    "兌": {"binary": "110", "symbol": "☱", "nature": "澤 (Lake)", "element": "金"},
    "艮": {"binary": "001", "symbol": "☶", "nature": "山 (Mountain)", "element": "土"},
    "離": {"binary": "101", "symbol": "☲", "nature": "火 (Fire)", "element": "火"},
    "巽": {"binary": "011", "symbol": "☴", "nature": "風 (Wind)", "element": "木"},
    "乾": {"binary": "111", "symbol": "☰", "nature": "天 (Heaven)", "element": "金"},
}


class HexagramMeta(dict):
    """
    Hexagram metadata container supporting dict indexing, attribute access,
    and tuple unpacking for backwards compatibility.
    """

    def __init__(
        self,
        number: int,
        name: str,
        nature: str,
        pinyin: str,
        thai: str,
        judgment: str,
        upper_trigram: str,
        lower_trigram: str,
        binary: str,
    ):
        data = {
            "number": number,
            "name": name,
            "nature": nature,
            "pinyin": pinyin,
            "thai": thai,
            "judgment": judgment,
            "upper_trigram": upper_trigram,
            "lower_trigram": lower_trigram,
            "binary": binary,
        }
        super().__init__(data)
        self.number = number
        self.name = name
        self.nature = nature
        self.pinyin = pinyin
        self.thai = thai
        self.judgment = judgment
        self.upper_trigram = upper_trigram
        self.lower_trigram = lower_trigram
        self.binary = binary

    def __iter__(self):
        # Tuple unpacking: (name, nature, pinyin, thai, judgment)
        return iter((self.name, self.nature, self.pinyin, self.thai, self.judgment))

    def __getitem__(self, item: Any) -> Any:
        if isinstance(item, int):
            return (self.name, self.nature, self.pinyin, self.thai, self.judgment)[item]
        return super().__getitem__(item)


# Raw 64 Hexagram Definitions (King Wen sequence 1-64)
# (number, name, nature, pinyin, thai, judgment, upper_trigram, lower_trigram, binary)
_RAW_64_HEXAGRAMS: list[tuple[int, str, str, str, str, str, str, str, str]] = [
    (1, "乾為天", "大吉", "Qián Wéi Tiān", "เฉียนเหวยเทียน (ฟ้าสร้างสรรค์)", "元亨利貞。天行健，君子以自強不息。", "乾", "乾", "111111"),
    (2, "坤為地", "順利", "Kūn Wéi Dì", "คุนเหวยตี้ (ดินเกื้อหนุน)", "地勢坤，君子以厚德載物。", "坤", "坤", "000000"),
    (3, "水雷屯", "宜守", "Shuǐ Léi Zhūn", "สุ่ยเหลยจุน (ความยากลำบากเริ่มต้น)", "雲雷屯，君子以經綸。剛柔始交而難生。", "坎", "震", "100010"),
    (4, "山水蒙", "啓蒙", "Shān Shuǐ Méng", "ซานสุ่ยเหมิง (เยาว์วัย ไร้เดียงสา)", "山下出泉，蒙。君子以果行育德。", "艮", "坎", "010001"),
    (5, "水天需", "等待", "Shuǐ Tiān Xū", "สุ่ยเทียนซวี (การรอคอยอย่างใจเย็น)", "雲上於天，需。君子以飲食宴樂。", "坎", "乾", "111010"),
    (6, "天水訟", "謹慎", "Tiān Shuǐ Sòng", "เทียนสุ่ยซ่ง (ความขัดแย้ง คดีความ)", "天與水違行，訟。君子以作事謀始。", "乾", "坎", "010111"),
    (7, "地水師", "律己", "Dì Shuǐ Shī", "ตี้สุ่ยซือ (กองทัพ วินัย)", "地中有水，師。君子以容民畜眾。", "坤", "坎", "010000"),
    (8, "水地比", "親和", "Shuǐ Dì Bǐ", "สุ่ยตี้ปี่ (ความสามัคคี พันธมิตร)", "地上有水，比。先王以建萬國，親諸侯。", "坎", "坤", "000010"),
    (9, "風天小畜", "積蓄", "Fēng Tiān Xiǎo Xù", "เฟิงเทียนเสี่ยวชวี่ (สะสมพลังเล็กน้อย)", "風行天上，小畜。君子以懿文德。", "巽", "乾", "111011"),
    (10, "天澤履", "禮儀", "Tiān Zé Lǚ", "เทียนเจ๋อลวี่ (การดำเนินตามมารยาท)", "上天下澤，履。君子以辯上下，定民志。", "乾", "兌", "110111"),
    (11, "地天泰", "通達", "Dì Tiān Tài", "ตี้เทียนไท่ (ความเจริญ รุ่งเรือง สมบูรณ์)", "天地交，泰。后以財成天地之道，輔相天地之宜。", "坤", "乾", "111000"),
    (12, "天地否", "閉塞", "Tiān Dì Pǐ", "เทียนตี้ผี่ (ความติดขัด ถดถอย)", "天地不交，否。君子以儉德辟難，不可榮以祿。", "乾", "坤", "000111"),
    (13, "天火同人", "和諧", "Tiān Huǒ Tóng Rén", "เทียนหั่วถงเหริน (ความสามัคคี มิตรสหาย)", "天與火，同人。君子以類族辨物。", "乾", "離", "101111"),
    (14, "火天大有", "豐盛", "Huǒ Tiān Dà Yǒu", "หั่วเทียนต้าโหย่ว (ความอุดมสมบูรณ์ยิ่งใหญ่)", "火在天上，大有。君子以遏惡揚善，順天休命。", "離", "乾", "111101"),
    (15, "地山謙", "謙遜", "Dì Shān Qiān", "ตี้ซานเชียน (ความถ่อมตน อ่อนน้อม)", "地中有山，謙。君子以裒多益寡，稱物平施。", "坤", "艮", "001000"),
    (16, "雷地豫", "喜悅", "Léi Dì Yù", "เหลยตี้ยู่ (ความเบิกบาน ยินดี)", "雷出地奮，豫。先王以作樂崇德，殷薦之上帝。", "震", "坤", "000100"),
    (17, "澤雷隨", "隨和", "Zé Léi Suí", "เจ๋อเหลยสุย (การคล้อยตาม ปรับตัว)", "澤中有雷，隨。君子以嚮晦入宴息。", "兌", "震", "100110"),
    (18, "山風蠱", "整頓", "Shān Fēng Gǔ", "ซานเฟิงกู่ (การแก้ไข ปรับปรุงสิ่งชำรุด)", "山下有風，蠱。君子以振民育德。", "艮", "巽", "011001"),
    (19, "地澤臨", "督導", "Dì Zé Lín", "ตี้เจ๋อหลิน (การเข้ามา ดูแลอย่างใกล้ชิด)", "地上有澤，臨。君子以教思無窮，容保民無疆。", "坤", "兌", "110000"),
    (20, "風地觀", "觀察", "Fēng Dì Guān", "เฟิงตี้กวาน (การสังเกต พิจารณา สำรวจ)", "風行地上，觀。先王以省方觀民設教。", "巽", "坤", "000011"),
    (21, "火雷噬嗑", "決斷", "Huǒ Léi Shì Kè", "หั่วเหลยซื่อเค่อ (การขบกัด กำจัดสิ่งกีดขวาง)", "雷電噬嗑。先王以明罰敕法。", "離", "震", "100101"),
    (22, "山火賁", "文飾", "Shān Huǒ Bì", "ซานหั่วปี้ (ความงดงาม การประดับตกแต่ง)", "山下有火，賁。君子以明庶政，無敢折獄。", "艮", "離", "101001"),
    (23, "山地剝", "剝落", "Shān Dì Bō", "ซานตี้โป (การหลุดลอก เสื่อมถอย)", "山附於地，剝。上以厚下安宅。", "艮", "坤", "000001"),
    (24, "地雷復", "復興", "Dì Léi Fù", "ตี้เหลยฟู่ (การหวนคืน ฟื้นฟูชีพใหม่)", "雷在地中，復。先王以至日閉關，商旅不行。", "坤", "震", "100000"),
    (25, "天雷無妄", "真誠", "Tiān Léi Wú Wàng", "เทียนเหลยอู๋ว่าง (ความซื่อตรง ไร้ความหลอกลวง)", "天下雷行，物與無妄。先王以茂對時育萬物。", "乾", "震", "100111"),
    (26, "山天大畜", "大蓄", "Shān Tiān Dà Xù", "ซานเทียนต้าชวี่ (การสะสมพลังมหาศาล)", "天在山中，大畜。君子以多識前言往行，以畜其德。", "艮", "乾", "111001"),
    (27, "山雷頤", "養育", "Shān Léi Yí", "ซานเหลยอี๋ (การบำรุง เลี้ยงดู รักษาสุขภาพ)", "山下有雷，頤。君子以慎言語，節飲食。", "艮", "震", "100001"),
    (28, "澤風大過", "負擔", "Zé Fēng Dà Guò", "เจ๋อเฟิงต้ากั้ว (แบกรับภาระหนักเกินกำลัง)", "澤滅木，大過。君子以獨立不懼，遁世無悶。", "兌", "巽", "011110"),
    (29, "坎為水", "險阻", "Kǎn Wéi Shuǐ", "ข่านเหวยสุ่ย (อันตราย หลุมพราง สายน้ำ)", "水洊至，習坎。君子以常德行，習教事。", "坎", "坎", "010010"),
    (30, "離為火", "光明", "Lí Wéi Huǒ", "หลีเหวยหั่ว (ความสว่าง พลังไฟ การยึดเกาะ)", "明兩作，離。大人以繼明照于四方。", "離", "離", "101101"),
    (31, "澤山咸", "感應", "Zé Shān Xián", "เจ๋อซานเสียน (ความผูกพัน เหนี่ยวนำใจ)", "山上有澤，咸。君子以虛受人。", "兌", "艮", "001110"),
    (32, "雷風恆", "恆久", "Léi Fēng Héng", "เหลยเฟิงเหิง (ความมั่นคง ยั่งยืน ต่อเนื่อง)", "雷風，恆。君子以立不易方。", "震", "巽", "011100"),
    (33, "天山遯", "隱退", "Tiān Shān Dùn", "เทียนซานต้วน (การหลบลี้ ถอยฉาก)", "天下有山，遯。君子以遠小人，不惡而嚴。", "乾", "艮", "001111"),
    (34, "雷天大壯", "剛強", "Léi Tiān Dà Zhuàng", "เหลยเทียนต้าจ้วง (พลังอำนาจอันกล้าแกร่ง)", "雷在天上，大壯。君子以非禮弗履。", "震", "乾", "111100"),
    (35, "火地晉", "前進", "Huǒ Dì Jìn", "หั่วตี้จิ้น (ความก้าวหน้า รุ่งโรจน์)", "明出地上，晉。君子以自昭明德。", "離", "坤", "000101"),
    (36, "地火明夷", "晦暗", "Dì Huǒ Míng Yí", "ตี้หั่วหมิงอี๋ (แสงสว่างถูกบดบัง ซ่อนประกาย)", "明入地中，明夷。君子以蒞眾，用晦而明。", "坤", "離", "101000"),
    (37, "風火家人", "治家", "Fēng Huǒ Jiā Rén", "เฟิงหั่วเจียเหริน (ความสัมพันธ์ในครอบครัว)", "風自火出，家人。君子以言有物而行有恆。", "巽", "離", "101011"),
    (38, "火澤睽", "乖異", "Huǒ Zé Kuí", "หั่วเจ๋อขุย (ความแปลกแยก แตกต่าง)", "上火下澤，睽。君子以同而異。", "離", "兌", "110101"),
    (39, "水山蹇", "艱難", "Shuǐ Shān Jiǎn", "สุ่ยซานเจี่ยน (ความยากลำบาก หนทางตัน)", "山上有水，蹇。君子以反身修德。", "坎", "艮", "001010"),
    (40, "雷水解", "緩解", "Léi Shuǐ Xiè", "เหลยสุ่ยเซี่ย (การคลี่คลาย ปลดปล่อย)", "雷雨作，解。君子以赦過宥罪。", "震", "坎", "010100"),
    (41, "山澤損", "減損", "Shān Zé Sǔn", "ซานเจ๋อสุ่น (การเสียสละ ลดทอนสิ่งเกิน)", "山下有澤，損。君子以懲忿窒慾。", "艮", "兌", "110001"),
    (42, "風雷益", "增益", "Fēng Léi Yì", "เฟิงเหลยอี้ (การเพิ่มพูน ผลประโยชน์ งอกงาม)", "風雷，益。君子以見善則遷，有過則改。", "巽", "震", "100011"),
    (43, "澤天夬", "決裂", "Zé Tiān Guài", "เจ๋อเทียนไกว้ (การตัดสินใจเด็ดขาด ขจัดสิ่งชั่ว)", "澤上於天，夬。君子以施祿及下，居德則忌。", "兌", "乾", "111110"),
    (44, "天風姤", "相遇", "Tiān Fēng Gòu", "เทียนเฟิงโก้ว (การพบพานโดยบังเอิญ ระวังสิ่งแทรกแซง)", "天下有風，姤。后以施命誥四方。", "乾", "巽", "011111"),
    (45, "澤地萃", "聚集", "Zé Dì Cuì", "เจ๋อตี้ชุ่ย (การชุมนุม รวมตัวของหมู่คณะ)", "澤上於地，萃。君子以除戎器，戒不虞。", "兌", "坤", "000110"),
    (46, "地風升", "上升", "Dì Fēng Shēng", "ตี้เฟิงเซิง (การเติบโต ไต่เต้าขึ้นสู่ที่สูง)", "地中生木，升。君子以順德，積小以高大。", "坤", "巽", "011000"),
    (47, "澤水困", "困頓", "Zé Shuǐ Kùn", "เจ๋อสุ่ยคุ่น (ความยากลำบาก ติดขัด คับขัน)", "澤無水，困。君子以致命遂志。", "兌", "坎", "010110"),
    (48, "水風井", "井養", "Shuǐ Fēng Jǐng", "สุ่ยเฟิงจิ่ง (บ่อน้ำ การหล่อเลี้ยงผู้คน)", "木上有水，井。君子以勞民勸相。", "坎", "巽", "011010"),
    (49, "澤火革", "變革", "Zé Huǒ Gé", "เจ๋อหั่วเก๋อ (การปฏิรูป เปลี่ยนแปลงสิ่งเดิม)", "澤中有火，革。君子以治曆明時。", "兌", "離", "101110"),
    (50, "火風鼎", "鼎新", "Huǒ Fēng Dǐng", "หั่วเฟิงติ่ง (กระถางสำริด สถาปนาสิ่งใหม่)", "木上有火，鼎。君子以正位凝命。", "離", "巽", "011101"),
    (51, "震為雷", "震動", "Zhèn Wéi Léi", "เจิ้นเหวยเหลย (ฟ้าร้องกึกก้อง สติในการตื่นตัว)", "洊雷，震。君子以恐懼脩省。", "震", "震", "100100"),
    (52, "艮為山", "止息", "Gèn Wéi Shān", "เกิ้นเหวยซาน (ภูเขาสงบ การหยุดนิ่ง สงบใจ)", "兼山，艮。君子以思不出其位。", "艮", "艮", "001001"),
    (53, "風山漸", "循序", "Fēng Shān Jiàn", "เฟิงซานเจี้ยน (ความก้าวหน้าทีละก้าว นุ่มนวล)", "山上有木，漸。君子以居賢德善俗。", "巽", "艮", "001011"),
    (54, "雷澤歸妹", "戒慎", "Léi Zé Guī Mèi", "เหลยเจ๋อกุยเม่ย (การวิวาห์ของหญิงสาว ระวังความใจร้อน)", "澤上有雷，歸妹。君子以永終知敝。", "震", "兌", "110100"),
    (55, "雷火豐", "豐大", "Léi Huǒ Fēng", "เหลยหั่วเฟิง (ความอุดมสมบูรณ์สูงสุด จุดพีค)", "雷電皆至，豐。君子以折獄致刑。", "震", "離", "101100"),
    (56, "火山旅", "羈旅", "Huǒ Shān Lǚ", "หั่วซานลวี่ (คนพเนจร การเดินทาง ต่างถิ่น)", "山上有火，旅。君子以明慎用刑，而不留獄。", "離", "艮", "001101"),
    (57, "巽為風", "順應", "Xùn Wéi Fēng", "ซวิ่นเหวยเฟิง (สายลมพัดผ่าน การแทรกซึม นุ่มนวล)", "隨風，巽。君子以申命行事。", "巽", "巽", "011011"),
    (58, "兌為澤", "愉悅", "Duì Wéi Zé", "ตุ้ยเหวยเจ๋อ (บึงน้ำ ความเบิกบาน มิตรภาพ)", "麗澤，兌。君子以朋友講習。", "兌", "兌", "110110"),
    (59, "風水渙", "渙散", "Fēng Shuǐ Huàn", "เฟิงสุ่ยฮ่วน (การสลายตัว กระจัดกระจาย พ้นวิกฤต)", "風行水上，渙。先王以享于帝立廟。", "巽", "坎", "010011"),
    (60, "水澤節", "節制", "Shuǐ Zé Jié", "สุ่ยเจ๋อเจี๋ย (การประหยัด ความพอดี การควบคุมขอบเขต)", "澤上有水，節。君子以制數度，議德行。", "坎", "兌", "110010"),
    (61, "風澤中孚", "誠信", "Fēng Zé Zhōng Fú", "เฟิงเจ๋อจงฝู (ความจริงใจ ศรัทธาอันบริสุทธิ์)", "澤上有風，中孚。君子以議獄緩死。", "巽", "兌", "110011"),
    (62, "雷山小過", "小過", "Léi Shān Xiǎo Guò", "เหลยซานเสี่ยวกั้ว (การก้าวล่วงเล็กน้อย ระมัดระวัง)", "山上有雷，小過。君子以行過乎恭，喪過乎哀，用過乎儉。", "震", "艮", "001100"),
    (63, "水火既濟", "圓滿", "Shuǐ Huǒ Jì Jì", "สุ่ยหั่วจี้จี้ (สำเร็จเสร็จสิ้น สมบูรณ์ลงตัว)", "水在火上，既濟。君子以思患而預防之。", "坎", "離", "101010"),
    (64, "火水未濟", "未完", "Huǒ Shuǐ Wèi Jì", "หั่วสุ่ยเว่ยจี้ (ยังไม่สิ้นสุด การเริ่มต้นวัฏจักรใหม่)", "火在水上，未濟。君子以慎辨物居方。", "離", "坎", "010101"),
]

# Build comprehensive 64 Hexagram lookup dictionary with multi-key indexing:
# - 6-bit binary string ('111111' - '000000')
# - Tuple of 6 bits ((1, 1, 1, 1, 1, 1))
# - Integer (1 to 64)
# - Lower/Upper Trigram name tuple (('乾', '乾'))
HEXAGRAM_64_NAMES: dict[Any, HexagramMeta] = {}

for entry in _RAW_64_HEXAGRAMS:
    meta = HexagramMeta(*entry)
    # Primary binary string key (bottom-to-top)
    HEXAGRAM_64_NAMES[meta.binary] = meta
    # King Wen number (1-64)
    HEXAGRAM_64_NAMES[meta.number] = meta
    # 6-bit integer tuple
    bit_tuple = tuple(int(b) for b in meta.binary)
    HEXAGRAM_64_NAMES[bit_tuple] = meta
    # Lower, Upper trigram pair tuple
    HEXAGRAM_64_NAMES[(meta.lower_trigram, meta.upper_trigram)] = meta

FIVE_RELATIVES = ["父母", "兄弟", "子孫", "妻財", "官鬼"]
SIX_ANIMALS = ["青龍", "朱雀", "勾陳", "騰蛇", "白虎", "玄武"]

DAY_STEM_SIX_ANIMALS_START = {
    "甲": "青龍", "乙": "青龍",
    "丙": "朱雀", "丁": "朱雀",
    "戊": "勾陳",
    "己": "騰蛇",
    "庚": "白虎", "辛": "白虎",
    "壬": "玄武", "癸": "玄武",
}


class IChingEngine(AbstractAstrologyEngine):
    """Core I Ching & Liu Yao calculation engine."""

    @property
    def engine_name(self) -> str:
        return "I Ching & Liu Yao Engine"

    @property
    def system_type(self) -> str:
        return "pu_shi"

    def cast_lines(self, seed: int | None = None) -> list[int]:
        """
        Cast 6 lines (bottom to top):
        6: Old Yin (動爻), 7: Young Yang, 8: Young Yin, 9: Old Yang (動爻).
        """
        if seed is not None:
            random.seed(seed)
        return [random.choice([6, 7, 8, 9]) for _ in range(6)]

    def lines_to_binary(self, lines: list[int]) -> tuple[str, str]:
        """
        Convert 6 lines to binary string representation for Primary & Transformed Hexagram.
        Yang (7, 9) = '1', Yin (6, 8) = '0'.
        Old Yang (9) changes to Yin '0', Old Yin (6) changes to Yang '1'.
        """
        primary_bits = []
        transformed_bits = []
        for line in lines:
            if line in (7, 9):
                primary_bits.append("1")
                transformed_bits.append("0" if line == 9 else "1")
            else:
                primary_bits.append("0")
                transformed_bits.append("1" if line == 6 else "0")
        return "".join(primary_bits), "".join(transformed_bits)

    def calculate_liu_yao(self, day_stem: str, lines: list[int]) -> EngineChartResult:
        """
        Calculate complete Liu Yao setup with Six Animals, Five Relatives,
        and full 64 Hexagrams judgment metadata.
        """
        primary_bits, transformed_bits = self.lines_to_binary(lines)
        primary_meta = HEXAGRAM_64_NAMES.get(
            primary_bits,
            HexagramMeta(0, "本卦", "吉", "Běn Guà", "เปิ่นกว้า (เค้าเดิม)", "本卦", "坤", "坤", primary_bits),
        )
        transformed_meta = HEXAGRAM_64_NAMES.get(
            transformed_bits,
            HexagramMeta(0, "變卦", "平", "Biàn Guà", "เปี้ยนกว้า (ผันแปร)", "變卦", "坤", "坤", transformed_bits),
        )

        # Six Animals starting from Day Stem
        start_animal = DAY_STEM_SIX_ANIMALS_START.get(day_stem, "青龍")
        start_idx = SIX_ANIMALS.index(start_animal)

        six_lines_detail = []
        for i in range(6):
            animal = SIX_ANIMALS[(start_idx + i) % 6]
            line_val = lines[i]
            line_type = "陽爻" if line_val in (7, 9) else "陰爻"
            is_moving = line_val in (6, 9)
            relative = FIVE_RELATIVES[i % 5]

            six_lines_detail.append({
                "line_number": i + 1,
                "line_value": line_val,
                "line_type": line_type,
                "is_moving": is_moving,
                "relative": relative,
                "animal": animal,
            })

        raw = {
            "engine": "IChingEngine",
            "day_stem": day_stem,
            "raw_lines": lines,
            "primary_hexagram": {
                "number": primary_meta.number,
                "binary": primary_bits,
                "name": primary_meta.name,
                "nature": primary_meta.nature,
                "pinyin": primary_meta.pinyin,
                "thai": primary_meta.thai,
                "judgment": primary_meta.judgment,
                "upper_trigram": primary_meta.upper_trigram,
                "lower_trigram": primary_meta.lower_trigram,
            },
            "transformed_hexagram": {
                "number": transformed_meta.number,
                "binary": transformed_bits,
                "name": transformed_meta.name,
                "nature": transformed_meta.nature,
                "pinyin": transformed_meta.pinyin,
                "thai": transformed_meta.thai,
                "judgment": transformed_meta.judgment,
                "upper_trigram": transformed_meta.upper_trigram,
                "lower_trigram": transformed_meta.lower_trigram,
            },
            "six_lines": six_lines_detail,
        }
        return EngineChartResult(
            engine_name=self.engine_name,
            system_type=self.system_type,
            chart_data=raw,
        )

    def calculate(self, *args: Any, **kwargs: Any) -> EngineChartResult:
        """Standard AbstractAstrologyEngine calculate entrypoint."""
        if "day_stem" in kwargs or "lines" in kwargs:
            day_stem = kwargs.get("day_stem", "甲")
            lines = kwargs.get("lines") or self.cast_lines(kwargs.get("seed"))
            return self.calculate_liu_yao(day_stem, lines)
        if len(args) >= 2 and isinstance(args[0], str) and isinstance(args[1], list):
            return self.calculate_liu_yao(args[0], args[1])
        if len(args) == 1:
            if isinstance(args[0], list):
                return self.calculate_liu_yao("甲", args[0])
            elif isinstance(args[0], str):
                return self.calculate_liu_yao(args[0], self.cast_lines())
        return self.calculate_liu_yao("甲", self.cast_lines())


if __name__ == "__main__":
    ic = IChingEngine()
    lines = ic.cast_lines(seed=42)
    chart = ic.calculate_liu_yao("甲", lines)
    print(chart)

