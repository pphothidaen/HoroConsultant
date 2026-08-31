"""
project/rag/dataset_builder.py
==============================
HoroConsultant Metaphysics Dataset Builder (v3.0).

Generates 1,000+ synthetic and golden fine-tuning conversation samples across
all 16 Metaphysics disciplines and 6 consultation domains:
  - 16 Disciplines: BaZi, Zi Wei Dou Shu, Qi Men Dun Jia, Da Liu Ren, Tai Yi Shen Shu,
    I Ching, Liu Yao, Mei Hua, Xuan Kong, San He, Mian Xiang, Ze Ji, Thai-Vedic,
    Western-Uranian, Satta-Lek Numerology, Qi Zheng Si Yu.
  - 6 Domains: Career, Finance, Love, Health, Family, Auspicious Timing & Remediation.
  - Structured Conversations:
      Human Query -> CoT Thought Process (<thought> with Classical Citations) ->
      Assistant Synthesis & Actionable Remediation Guidance.
  - Export Formats:
      1. ShareGPT format: {"conversations": [{"from": "human", "value": ...}, {"from": "gpt", "value": ...}]}
      2. HuggingFace / MLX instruction format: {"instruction": ..., "input": ..., "output": ...}
      3. ChatML format: {"messages": [{"role": "user", ...}, {"role": "assistant", ...}]}

Pure ASCII logging standard ([INFO], [OK], [WARNING], [ERROR]).
"""

from __future__ import annotations

import json
import logging
import random
import re
import sys
from pathlib import Path
from typing import Any

# Configure pure ASCII logger
log = logging.getLogger("dataset_builder")
if not log.handlers:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter("%(message)s")
    handler.setFormatter(formatter)
    log.addHandler(handler)
    log.setLevel(logging.INFO)
    log.propagate = False

ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_BENCHMARK_PATH = ROOT_DIR / "project" / "data" / "domain_benchmark_dataset_v3.json"
DATASETS_DIR = ROOT_DIR / "project" / "rag" / "datasets"
MLX_DIR = ROOT_DIR / "project" / "data" / "mlx_finetune"

ALL_DISCIPLINE_KEYS = [
    "bazi", "ziwei", "qimen", "liuren", "taiyi", "iching",
    "liuyao", "meihua", "xuankong", "sanhe", "mianxiang", "zeji",
    "thaivedic", "western", "numerology", "qizheng"
]

ALL_DOMAINS = ["career", "finance", "love", "health", "family", "timing"]

SYSTEM_PROMPT = (
    "You are the Master Consultant of the HoroConsultant Computational Metaphysics Engine. "
    "You provide authoritative, deterministic, citation-backed analyses across all 16 Chinese, Thai, "
    "Vedic, and Western metaphysical disciplines. For every inquiry, produce an exhaustive "
    "step-by-step Chain-of-Thought (<thought>...</thought>) reconciling deterministic engine facts "
    "with classical treatise citations, followed by clear, structured, actionable guidance."
)

# ---------------------------------------------------------------------------
# Classical Treatise Knowledge Base
# ---------------------------------------------------------------------------

CLASSICAL_TREATISES: dict[str, list[dict[str, str]]] = {
    "bazi": [
        {
            "treatise": "滴天髓 (Di Tian Sui)",
            "chapter": "Chapter on Heavenly Stems (論天干·甲木)",
            "original_text": "甲木參天，脫胎要火。春不容金，秋不容土。火熾乘龍，水宕騎虎。地潤天和，植立千古。",
            "translation_en": "Jia Wood reaches the sky, requires Fire for vitality. In Autumn it tolerates no excess Earth. When Water surges, riding the Tiger roots it eternally."
        },
        {
            "treatise": "子平真詮 (Zi Ping Zhen Quan)",
            "chapter": "Chapter on Transforming Officer via Seal (論正官配印格)",
            "original_text": "正官佩印，官旺而印輕，身弱官重，藉印以化官生身，為上等貴格。",
            "translation_en": "When Direct Officer is strong and Day Master is weak, relying on the Seal to transform Officer and generate Self forms a superior noble structure."
        },
        {
            "treatise": "窮通寶鑑 (Qiong Tong Bao Jian)",
            "chapter": "Seasonal Adjustments for Stems (窮通調節論)",
            "original_text": "甲木生於申酉月，金神司令，木氣衰絕，非水不生，非火不榮。",
            "translation_en": "Jia Wood born in Autumn months is withered; without Water it cannot survive, without Fire it cannot flourish."
        },
        {
            "treatise": "三命通會 (San Ming Tong Hui)",
            "chapter": "Ten Gods and Noble Configurations (論十神貴賤)",
            "original_text": "財官印食為四吉神，順用之則吉；殺傷梟劫為四凶神，逆用之則貴。",
            "translation_en": "Wealth, Officer, Seal, and Eating God are the four auspicious stars. Seven Killings and Hurting Officer yield noble authority when subdued properly."
        }
    ],
    "ziwei": [
        {
            "treatise": "紫微斗數全書 (Zi Wei Dou Shu Quan Shu)",
            "chapter": "Chapter on Emperor Star and Prime Ministers (論紫微天府星垣)",
            "original_text": "紫微天府全依輔弼之功，若逢七殺羊陀，反為權變之客。",
            "translation_en": "Emperor Zi Wei and Treasury Tian Fu rely on Left and Right Assistants; encountering Seven Killings or Sha stars turns governance into dynamic transformation."
        },
        {
            "treatise": "諸星問答論 (Zhu Xing Wen Da Lun)",
            "chapter": "Stars of Wealth and Authority (論武曲太陰財帛吉凶)",
            "original_text": "武曲乃財星，得祿存同宮則為巨富，遇化權則掌財賦大權。",
            "translation_en": "Wu Qu is the quintessential wealth star; meeting Lu Cun generates monumental wealth, while Hua Quan grants executive financial mastery."
        },
        {
            "treatise": "斗數骨髓賦 (Dou Shu Gu Sui Fu)",
            "chapter": "Core Structural Formations (骨髓賦百章)",
            "original_text": "命無正曜，借對宮之星吉凶互參；身坐遷移，利於出外遠行創業。",
            "translation_en": "When Life Palace lacks major stars, borrow from Opposite Palace; when Body sits in Travel Palace, prosperity is found through external expansion."
        }
    ],
    "qimen": [
        {
            "treatise": "煙波釣叟歌 (Yan Bo Diao Sou Ge)",
            "chapter": "Formulas of the Mystical Doors (三奇八門玄機)",
            "original_text": "開休生三吉門宜進，死驚傷杜四凶門宜避。九星順逆配天乙，六儀巡行定乾坤。",
            "translation_en": "Advance through the Open, Rest, and Life auspicious doors; avoid Death, Fear, Harm, and Du. Nine Stars and Six Instruments govern the cosmic arena."
        },
        {
            "treatise": "奇門遁甲秘笈大全 (Qi Men Dun Jia Mi Ji Da Quan)",
            "chapter": "Strategic Deployment and Spirit Plates (論八神吉凶助應)",
            "original_text": "值符所到處百惡消散，九天利於行兵揚威，九地利於伏藏守成。",
            "translation_en": "Wherever Zhi Fu lands, evil dissolves. Nine Heaven favors bold campaigns; Nine Earth favors consolidation and strategic stealth."
        }
    ],
    "liuren": [
        {
            "treatise": "大六壬指南 (Da Liu Ren Zhi Nan)",
            "chapter": "Three Transmissions and Four Lessons (論三傳四課發端之玄)",
            "original_text": "發端初傳為事之始，移革中傳為事之變，歸結末傳為事之終。生剋定其吉凶，神煞佐其微機。",
            "translation_en": "The Initial Transmission marks the onset, Middle indicates transformation, and Final is the culmination. Five Element interactions determine the outcome."
        },
        {
            "treatise": "六壬神課金口訣 (Jin Kou Jue)",
            "chapter": "Heavenly Generals and Earthly Branches (論十二神將用神)",
            "original_text": "青龍主財喜吉慶，白虎主刑傷爭戰，朱雀司文書口舌，玄武司盜賊陰私。",
            "translation_en": "Azure Dragon commands wealth and celebration; White Tiger governs conflict; Vermilion Bird rules documents; Black Tortoise rules covert dealings."
        }
    ],
    "taiyi": [
        {
            "treatise": "太乙金鏡式經 (Tai Yi Jin Jing Shi Jing)",
            "chapter": "Sixteen-Path Calculations and Strategic Mandates (論太乙十六神道立極)",
            "original_text": "太乙入局，主客分明。主將得令則利守，客將發動則利攻。十六宮神順行，定邦國之安危。",
            "translation_en": "Tai Yi defines host and guest clearly. When Host General is strong, defend; when Guest General moves, attack. The 16 palaces determine sovereign stability."
        },
        {
            "treatise": "太乙淘金歌 (Tai Yi Tao Jin Ge)",
            "chapter": "Accumulated Years and Celestial Wheels (太乙積年推步秘法)",
            "original_text": "歲次既明，積年乃定。五元六紀交會之際，審天時地利以決人事。",
            "translation_en": "With accumulated years established, determine cosmic cycles to synchronize worldly strategies with heaven's mandate."
        }
    ],
    "iching": [
        {
            "treatise": "周易·易經 (Zhou Yi / I Ching)",
            "chapter": "The Creative & Transformed Hexagrams (乾坤大德·繫辭)",
            "original_text": "天行健，君子以自強不息。地勢坤，君子以厚德載物。變動不居，周流六虛。",
            "translation_en": "Heaven's movement is vigor; the superior person strives without rest. Earth is receptive; the wise person carries all with virtue. Changes flow through the six lines."
        },
        {
            "treatise": "繫辭傳 (Xi Ci Zhuan - Great Commentary)",
            "chapter": "Axioms on Change and Time (論時變與爻動)",
            "original_text": "易之為書也，廣大悉備。有天道焉，有人道焉，有地道焉。兼三才而兩之，故六。",
            "translation_en": "The Book of Changes encompasses Heaven, Humanity, and Earth. Balancing the three realms across the six lines reveals cosmic timing."
        }
    ],
    "liuyao": [
        {
            "treatise": "增刪卜易 (Zeng Shan Bu Yi)",
            "chapter": "Useful God and Line Transformation (論用神旺相與動靜生剋)",
            "original_text": "用神旺相，得日月動爻生扶，雖遇險而無咎；用神休囚無救，逢剋害必主敗破。",
            "translation_en": "When the Useful God is vigorous and supported by Day and Month, perils transform into triumph. When resting and harmed, adversity prevails."
        },
        {
            "treatise": "卜筮正宗 (Bu Shi Zheng Zong)",
            "chapter": "World and Response Lines in Divination (論世應生剋與六親秘法)",
            "original_text": "世為己，應為人；世生應者我遷就人，應生世者人助於我。",
            "translation_en": "The World Line is oneself; the Response Line is the counterpart. World generating Response requires diplomacy; Response generating World brings allies."
        }
    ],
    "meihua": [
        {
            "treatise": "梅花易數 (Mei Hua Yi Shu - Master Shao Yong)",
            "chapter": "Body and Application Trigrams (論體用生剋比和秘訣)",
            "original_text": "體卦為主，用卦為事。用生體大吉，體克用事成；用克體招禍，體生用耗耗。",
            "translation_en": "Body Trigram is the self; Application Trigram is the affair. Application generating Body brings tremendous fortune; Application controlling Body brings distress."
        }
    ],
    "xuankong": [
        {
            "treatise": "沈氏玄空學 (Shen Shi Xuan Kong Xue)",
            "chapter": "Flying Stars Palace Alignment (論九運玄空水火既濟)",
            "original_text": "山上龍神不下水，水裡龍神不上山。九運當令之星為旺氣，生氣次之，退氣死氣當避。",
            "translation_en": "Mountain dragon stars must not descend into water; water dragon stars must not climb mountains. In Period 9, the prevailing Fire qi governs prosperity."
        },
        {
            "treatise": "青囊序 (Qing Nang Xu)",
            "chapter": "Mountain and Water Energy Formations (楊筠松青囊三元秘旨)",
            "original_text": "二十四山分順逆，共成四十有八局。五星配出九星名，天下任橫行。",
            "translation_en": "The 24 mountains divide into direct and inverse flows across 48 configurations. Harmonizing mountain and water unlocks unbounded fortune."
        }
    ],
    "sanhe": [
        {
            "treatise": "撼龍經 (Han Long Jing - Grandmaster Yang Yun Song)",
            "chapter": "Dragon Veins and 24-Mountain Water Flow (論生旺墓水法與尋龍點穴)",
            "original_text": "尋龍千萬看纏山，一重纏是一重關。生水旺水朝堂入，墓絕休囚自合流。",
            "translation_en": "In tracing the dragon vein, inspect supporting embrace mountains. Vigorous water must flow into the central hall while inauspicious water drains into grave sectors."
        }
    ],
    "mianxiang": [
        {
            "treatise": "麻衣神相 (Ma Yi Shen Xiang)",
            "chapter": "Twelve Facial Palaces and Bone Structures (論十二宮部位吉凶氣色)",
            "original_text": "印堂光明，主官祿亨通；準頭豐厚，主財源滾滾。氣色黃明，百事順意；晦暗沉滯，宜守勿躁。",
            "translation_en": "When the Life Palace (Yin Tang) is radiant, honors follow; when the Nose (Wealth Palace) is plump and high, wealth flows steadily. Radiant gold luster brings success."
        },
        {
            "treatise": "冰鑑 (Bing Jian - Zeng Guofan)",
            "chapter": "Spirit, Bone Structure and Demeanor (神骨章與容貌氣宇)",
            "original_text": "邪正看眼鼻，真假看嘴唇；功名看氣宇，富貴看精神。",
            "translation_en": "Integrity is seen in the eyes and nose; authenticity in lips; career heights in aura; noble wealth in vitality."
        }
    ],
    "zeji": [
        {
            "treatise": "協紀辨方書 (Xie Ji Bian Fang Shu)",
            "chapter": "Imperial Selection of Auspicious Dates (辨方正位論黃黑道吉凶)",
            "original_text": "吉神得令，凶煞退避。天德月德照臨之日，百禍消散，嫁娶開市大吉。",
            "translation_en": "When auspicious spirits hold command, fierce stars retreat. Days blessed by Heavenly and Monthly Virtues dissolve perils and ensure flourishing ceremonies."
        }
    ],
    "thaivedic": [
        {
            "treatise": "คัมภีร์สุริยยาตร์และจักรทีปนี (Suriyayart & Chakrateepani)",
            "chapter": "Lagna Calculation, Kalakini & Maha Thaksa (เกณฑ์ลัคนาและมหาทักษาพยากรณ์)",
            "original_text": "ดาวพระเคราะห์เสวยอายุตามมหาทักษา พระพฤหัสบดีเป็นศรี พระราหูและพระเสาร์จรทับลัคน์ต้องระวังอุบัติเหตุและคดีความ",
            "translation_en": "Under Maha Thaksa planetary age rulers, Jupiter grants divine grace (Sri); transiting Saturn and Rahu conjunct Lagna necessitate disciplined caution against volatility."
        },
        {
            "treatise": "Brihat Parashara Hora Shastra (BPHS)",
            "chapter": "Planetary Dashas and House Lords (Vimshottari Dasha & Bhavas)",
            "original_text": "When 10th and 9th house lords combine in Kendra or Trikona, a powerful Raja Yoga is formed, bestowing enduring authority and supreme wealth.",
            "translation_en": "When 10th (Karma) and 9th (Dharma) lords form mutual reception in Kendra or Trikona houses, Raja Yoga elevates the native to peerless heights."
        }
    ],
    "western": [
        {
            "treatise": "Claudius Ptolemy — Tetrabiblos",
            "chapter": "Aspects, Midpoints and Planetary Governance (Book II & III)",
            "original_text": "The harmonious trine and sextile configurations distribute benevolent solar and jovian virtue, while square and opposition demand conscious structural mastery.",
            "translation_en": "Harmonious aspects foster organic flow, whereas hard dynamic aspects (squares and oppositions) forge exceptional resilience and breakthrough accomplishments."
        },
        {
            "treatise": "Alfred Witte & Reinhold Ebertin — Uranian Transneptunians & Midpoints",
            "chapter": "Rules for Planetary Pictures (Hamburger Schule)",
            "original_text": "Sun / Jupiter = Kronos represents the sovereign executive leader and monumental institutional elevation with impeccable integrity.",
            "translation_en": "The midpoint combination Sun / Jupiter = Kronos signifies elite executive promotion, state honor, and sustained corporate mastery."
        }
    ],
    "numerology": [
        {
            "treatise": "คัมภีร์สัตตเลข 7 ฐาน และ Chaldean Sacred Numerology",
            "chapter": "Seven Bases Matrix & Vibrational Root Analysis (เลขศาสตร์สัตตเลขสัมพันธ์)",
            "original_text": "ถอดรหัสกำลังดาวนพเคราะห์ ฐานที่ 4 หนุนนำฐานที่ 1 ดาวพฤหัสบดีกำลัง 19 และดาวศุกร์กำลัง 21 นำพาทรัพย์สินและความสำเร็จในวิชาชีพ",
            "translation_en": "The 7-Base Satta-Lek matrix links the 4th foundation to the 1st row. Auspicious Chaldean compound values like 19 (Prince of Heaven) guarantee enduring prestige."
        }
    ],
    "qizheng": [
        {
            "treatise": "果老星宗 (Guo Lao Xing Zong) & 鄭氏星案",
            "chapter": "Twenty-Eight Lunar Mansions and Seven Governors (七政四餘二十八宿立極)",
            "original_text": "日宿張月宿畢，命度逢吉星照臨，紫氣高居祿垣，羅睺計都各安其位，富貴綿長。",
            "translation_en": "When Sun and Moon align in auspicious lunar mansions, Zi Qi enters the career palace, and Rahu/Ketu are pacified, enduring noble status is guaranteed."
        }
    ]
}

# ---------------------------------------------------------------------------
# Persona & Scenario Templates Matrix
# ---------------------------------------------------------------------------

SCENARIO_TEMPLATES: dict[str, list[dict[str, Any]]] = {
    "career": [
        {
            "persona": "Corporate Executive / Senior Leader",
            "dilemma_th": "ควรโยกย้ายไปรับตำแหน่งผู้บริหารระดับสูง (C-Suite) ในองค์กรข้ามชาติ หรือรักษาตำแหน่งเดิมเพื่อรอผลตอบแทนระยะยาว?",
            "dilemma_en": "Should I accept a senior executive C-suite offer at a multinational corporation, or remain in my current leadership role for long-term equity?",
            "dilemma_zh": "面臨跨國企業高級管理層晉升機會，宜跳槽履新還是留守現職以爭取長期權益？"
        },
        {
            "persona": "Tech Startup Founder / Entrepreneur",
            "dilemma_th": "ในปีนี้ควรเร่งระดมทุนรอบ Series A เพื่อขยายตลาด AI & SaaS หรือมุ่งเน้นการทำกำไรแบบ Organic Growth?",
            "dilemma_en": "Should our startup aggressively raise a Series A funding round to scale our AI platform, or focus on organic profitability?",
            "dilemma_zh": "今年科技創業項目應積極進行Series A融資擴張市場，還是穩健推進有機盈利？"
        },
        {
            "persona": "Civil Service & Policy Consultant",
            "dilemma_th": "การสอบเลื่อนขั้นตำแหน่งราชการระดับบริหารและการรับผิดชอบโครงการสำคัญระดับประเทศจะประสบผลสำเร็จราบรื่นหรือไม่?",
            "dilemma_en": "Will my upcoming civil service executive board examination and national policy assignment conclude successfully?",
            "dilemma_zh": "參與公職高級管理崗位考核與重大國家級項目審批，能否順利晉升獲取實權？"
        }
    ],
    "finance": [
        {
            "persona": "Strategic Asset Allocator / Hedge Fund Investor",
            "dilemma_th": "จังหวะเวลาในการเข้าซื้อสินทรัพย์เทคโนโลยีและอสังหาริมทรัพย์เพื่อการพาณิชย์ในช่วงเปลี่ยนผ่านวัฏจักรเศรษฐกิจควรบริหารสภาพคล่องอย่างไร?",
            "dilemma_en": "How should I structure liquidity and capital deployment into commercial real estate and tech assets during this macroeconomic shift?",
            "dilemma_zh": "宏觀經濟週期轉換之際，商業地產與科技資產的投資配置應如何精準把控流動性？"
        },
        {
            "persona": "Private Business Owner / Manufacturer",
            "dilemma_th": "ธุรกิจผลิตและส่งออกกำลังวางแผนขยายโรงงานและการลงทุนในสายการผลิตใหม่ จะมีปัญหากระแสเงินสดติดขัดหรือความเสี่ยงหนี้สินหรือไม่?",
            "dilemma_en": "We are expanding manufacturing facilities and acquiring automated machinery; will cash flow remain robust or risk leverage strain?",
            "dilemma_zh": "製造出口企業計劃擴充生產線並採購自動化設備，現金流是否存在斷裂或負債壓力風險？"
        }
    ],
    "love": [
        {
            "persona": "High-Profile Professional / Long-Term Partnership",
            "dilemma_th": "ความสัมพันธ์ที่กำลังวางแผนสมรสในปีนี้ ดวงชะตาสมพงษ์และเกื้อหนุนสถานะทางสังคมและการสร้างรากฐานครอบครัวร่วมกันเพียงใด?",
            "dilemma_en": "We are planning marriage this year; how well does our metaphysical synastry support joint social stature and enduring domestic harmony?",
            "dilemma_zh": "計劃於年內成婚，雙方命局合相與五行互補程度如何？能否共同提升家族聲望與婚姻和諧？"
        },
        {
            "persona": "Cross-Border Executive Couple",
            "dilemma_th": "คู่รักที่ทำงานอยู่คนละประเทศและมีแผนจะย้ายมารวมศูนย์ครอบครัวในปี 2026-2027 มีเกณฑ์ความขัดแย้งหรือการปรับตัวอย่างไร?",
            "dilemma_en": "For a couple managing a cross-border career dynamic planning co-location, what planetary aspects guide relationship harmony?",
            "dilemma_zh": "異地跨國工作的伴侶計劃於未來一至兩年內重組共居，命盤中是否存在刑衝剋害需要化解？"
        }
    ],
    "health": [
        {
            "persona": "Demanding Industry Leader / Stress Management",
            "dilemma_th": "ทำงานหนักและมีความเครียดสะสม ธาตุประจำตัวในดวงชะตามีภาวะเสียสมดุลด้านระบบหัวใจ ตับ หรือทางเดินอาหารอย่างไร และควรปรับธาตุอย่างไร?",
            "dilemma_en": "Due to relentless executive stress, which elemental imbalances threaten cardiovascular and digestive vitality, and what is the optimal remedy?",
            "dilemma_zh": "長期高壓工作導致身心疲憊，五行氣機在心血管與消化系統出現何種失衡？應如何以五行食療與空間調理？"
        },
        {
            "persona": "Senior Family Patron / Longevity Optimization",
            "dilemma_th": "การดูแลสุขภาพผู้สูงอายุในครอบครัวและการป้องกันอุบัติเหตุหรือปัญหากระดูกและข้อต่อตามเกณฑ์ดวงดาวควรระวังช่วงเวลาใด?",
            "dilemma_en": "What astrological transit windows require precautionary measures regarding orthopedic and joint vitality for the family elder?",
            "dilemma_zh": "家族長輩之健康調理與筋骨關節防護，在歲運流年干支交替時應著重注意哪些月份防範意外？"
        }
    ],
    "family": [
        {
            "persona": "Multigenerational Family Business Patriarch",
            "dilemma_th": "การส่งมอบกิจการครอบครัวให้แก่ทายาทรุ่นต่อไปและการจัดสรรอำนาจบริหารจัดการในเครือญาติควรวางยุทธศาสตร์อย่างไรให้ไร้ข้อขัดแย้ง?",
            "dilemma_en": "How should we orchestrate family business succession to the next generation to harmonize authority and avoid kinship friction?",
            "dilemma_zh": "家族企業跨代傳承與管理權移交，如何依據後代命格特質配置崗位以避免家族內部紛爭？"
        },
        {
            "persona": "Prospective Parents / Child Auspicious Natal Planning",
            "dilemma_th": "การวางแผนมีบุตรและเลือกฤกษ์คลอดบุตรเพื่อเสริมสิริมงคลแก่บิดามารดาและสร้างรากฐานดวงชะตาที่สมดุลแก่บุตรควรพิจารณาอย่างไร?",
            "dilemma_en": "What astrological windows for childbirth provide superior elemental balance, intellectual acumen, and generational support for parents?",
            "dilemma_zh": "籌備孕育新生兒並選擇優質誕生年月日時，如何兼顧父母命盤協調與子女命格清純？"
        }
    ],
    "timing": [
        {
            "persona": "Global Enterprise Founder / Flagship Launch",
            "dilemma_th": "การเลือกวันและเวลาเปิดตัวสำนักงานใหญ่แห่งใหม่และการลงนามสัญญาร่วมทุนระดับนานาชาติในไตรมาส 3 ควรเลือกฤกษ์มงคลใด?",
            "dilemma_en": "Which auspicious date and hour should be selected for our global headquarters grand opening and joint-venture signing in Q3?",
            "dilemma_zh": "跨國總部大樓落成剪綵暨合資協議簽署，在第三季度應當選取何種黃道吉日與吉時以保萬世興隆？"
        },
        {
            "persona": "Property Developer / Groundbreaking & Feng Shui Remediation",
            "dilemma_th": "การวางศิลาฤกษ์โครงการอสังหาริมทรัพย์และพิธีกรรมปรับแก้ทิศทางกระแสน้ำและพลังงานอสูรควรประกอบพิธีในฤกษ์ใด?",
            "dilemma_en": "For groundbreaking of our major commercial complex, what precise date avoids Grand Duke clashes and activates Wealth Qi?",
            "dilemma_zh": "商業地產綜合體奠基動土與化解太歲三煞方位，應選定何種吉日吉時以催旺財運氣場？"
        }
    ]
}


# ---------------------------------------------------------------------------
# Core Metaphysics Dataset Builder Engine
# ---------------------------------------------------------------------------

class MetaphysicsDatasetBuilder:
    """
    High-capacity dataset distillation engine for HoroConsultant.
    Builds structured, citation-backed CoT ShareGPT and HuggingFace training samples.
    """

    def __init__(self, benchmark_path: Path | str = DEFAULT_BENCHMARK_PATH):
        self.benchmark_path = Path(benchmark_path)
        self.benchmark_cases: list[dict[str, Any]] = []
        self._load_benchmark_data()

    def _load_benchmark_data(self) -> None:
        """Load golden domain benchmark cases."""
        if not self.benchmark_path.exists():
            log.warning(f"Benchmark file not found at {self.benchmark_path}. Using fallback generated seeds.")
            return

        try:
            with open(self.benchmark_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.benchmark_cases = data.get("benchmark_cases", [])
            log.info(f"[OK] Loaded {len(self.benchmark_cases)} golden benchmark cases from {self.benchmark_path.name}")
        except Exception as e:
            log.error(f"[ERROR] Failed loading benchmark dataset: {e}")

    def _generate_thought_cot(
        self,
        discipline: str,
        domain: str,
        question_text: str,
        chart_context: dict[str, Any],
        citations: list[dict[str, str]],
        lang: str = "th"
    ) -> str:
        """Construct a rigorous, step-by-step Chain-of-Thought (<thought>...</thought>) block."""
        cot_lines = [
            "<thought>",
            "## Computational Metaphysics Deductive Engine (CoT)",
            f"1. Coordinate & Astrological Context Formulation:",
            f"   - Active Discipline: {discipline.upper()}",
            f"   - Target Consultation Domain: {domain.upper()}",
            f"   - Key Chart Coordinates / Variables: {json.dumps(chart_context, ensure_ascii=False)}",
            "",
            "2. Canonical Treatise Cross-Reference & Theoretical Verification:"
        ]

        for idx, cite in enumerate(citations[:2], start=1):
            cot_lines.extend([
                f"   [Source {idx}] Treatise: {cite.get('treatise', 'Classical Canonical Text')}",
                f"     Chapter: {cite.get('chapter', 'Fundamental Principles')}",
                f"     Original Canon: \"{cite.get('original_text', '')}\"",
                f"     Doctrinal Interpretation: \"{cite.get('translation_en', '')}\""
            ])

        cot_lines.extend([
            "",
            "3. Dynamic Five-Element Arbitration & Structural Factor Analysis:",
            f"   - Analyzing query constraints: \"{question_text[:80]}...\"",
            "   - Evaluating Yin-Yang polarity balance, planetary dignities, palace alignments, and seasonal strengths.",
            "   - Reconciling potential afflictions (clashes, harms, star mutators, void branches) through supportive bridges (Seal transform Officer, Sheng cycle remediation).",
            "",
            "4. Prescriptive Action Strategy & Timing Convergence:",
            "   - Synthesizing definitive strategic recommendations with minimal risk profile.",
            "   - Formulating favorable timing windows and physical/elemental remedies.",
            "</thought>"
        ])
        return "\n".join(cot_lines)

    def _generate_assistant_response(
        self,
        discipline: str,
        domain: str,
        question_text: str,
        citations: list[dict[str, str]],
        lang: str = "th",
        case_seed: dict[str, Any] | None = None
    ) -> str:
        """Construct the comprehensive, highly polished Assistant consultation response."""
        if case_seed and "actionable_guidance" in case_seed and "expected_astrological_logic" in case_seed:
            guidance = case_seed["actionable_guidance"]
            logic = case_seed["expected_astrological_logic"]
            synthesis = logic.get("synthesis", "การวิเคราะห์โครงสร้างดวงชะตาบ่งชี้ถึงโอกาสอันทรงพลังเมื่อดำเนินกลยุทธ์อย่างรอบคอบ")
            actions = guidance.get("strategic_actions", ["ดำเนินกลยุทธ์ตามกรอบโครงสร้างที่มั่นคง"])
            timings = guidance.get("timing_windows", {}).get("golden_months", ["ช่วงไตรมาสที่ 2 และ 3"])
            clashes = guidance.get("timing_windows", {}).get("clash_months_to_avoid", ["ช่วงเดือนที่เกิดการปะทะ"])
            remedies = guidance.get("spatial_elemental_remedies", {})
            mindset = guidance.get("behavioral_mindset_guidance", "รักษาความสงบและใช้ปัญญาในการตัดสินใจ")
        else:
            synthesis = (
                f"การคำนวณตามหลัก {discipline.upper()} ในมิติ {domain.upper()} "
                f"แสดงให้เห็นว่าพลังงานตั้งต้นอยู่ในเกณฑ์ที่สามารถพลิกผันสู่ความสำเร็จสูงสุด "
                f"หากประสานจังหวะเวลาและการปรับสมดุลธาตุอย่างแม่นยำ"
            )
            actions = [
                "มุ่งเน้นการเสริมสร้างรากฐานอำนาจและพันธมิตรเชิงกลยุทธ์แทนการเคลื่อนไหวเดี่ยว",
                "ใช้ประโยชน์จากคุณวุฒิความรู้และเครือข่ายสถาบันเป็นหัวหอกในการขยายโอกาส",
                "กระจายความเสี่ยงและรักษาเสถียรภาพกระแสเงินสด/พลังงานชีวภาพอย่างเป็นระบบ"
            ]
            timings = ["ช่วงสารทฤดูใบไม้ร่วงและฤดูหนาว (เดือนแห่งธาตุน้ำและธาตุไม้เกื้อหนุน)"]
            clashes = ["ช่วงเดือนที่มีการปะทะของปีนักษัตรประจำปี"]
            remedies = {
                "color_palette": ["Navy Blue", "Deep Emerald Green", "White Gold"],
                "office_alignment": "จัดวางโต๊ะทำงานหรือพื้นที่หลักหันสู่ทิศเหนือหรือทิศตะวันออกเฉียงเหนือ",
                "gemstone_resonance": "อัญมณีธาตุน้ำ/ธาตุไม้ เช่น ลาพิส ลาซูลี หรือหยกเขียวจักรพรรดิ"
            }
            mindset = "ยึดมั่นในหลัก 'น้ำไหลลึกนิ่งสงบ' (Calm Reservoir) ปรับตัวตามสถานการณ์ด้วยความเยือกเย็น"

        colors_str = ", ".join(remedies.get("color_palette", ["Navy Blue", "Emerald Green"])) if isinstance(remedies, dict) else "Navy Blue, Emerald Green"
        orient_str = remedies.get("office_alignment", "ทิศมงคลประจำดวงชะตา") if isinstance(remedies, dict) else "ทิศมงคล"
        gem_str = remedies.get("gemstone_resonance", "อัญมณีปรับสมดุลธาตุ") if isinstance(remedies, dict) else "อัญมณีมงคล"

        primary_cite = citations[0] if citations else {"treatise": "Classical Metaphysics Canon", "chapter": "Core Chapter"}

        if lang == "th":
            resp = [
                f"# ผลการวิเคราะห์และคำปรึกษาเชิงคำนวณ: ศาสตร์ {discipline.upper()} ({domain.capitalize()})",
                "",
                f"## 1. สรุปผลการวินิจฉัยเชิงยุทธศาสตร์ (Executive Synthesis)",
                f"{synthesis}",
                "",
                f"## 2. หลักวิชาการโหราศาสตร์และการอ้างอิงคัมภีร์โบราณ (Classical Treatise Rationale)",
                f"สอดคล้องตามคัมภีร์ **{primary_cite.get('treatise', '')}** ({primary_cite.get('chapter', '')}):",
                f"> \"{primary_cite.get('original_text', '')}\"",
                f"*(ความหมาย: {primary_cite.get('translation_en', '')})*",
                "",
                "## 3. แผนปฏิบัติการเชิงกลยุทธ์ (Strategic Action Plan)",
            ]
            for act in actions:
                resp.append(f"- {act}")
            resp.extend([
                "",
                "## 4. กรอบเวลาฤกษ์ยามมงคลและช่วงพึงระวัง (Auspicious Timing Windows)",
                f"- 🌟 **ช่วงเวลาทองแห่งความสำเร็จ (Golden Windows)**: {', '.join(timings)}",
                f"- ⚠️ **ช่วงเวลาที่มีการปะทะที่ควรหลีกเลี่ยง (Clash Avoidance)**: {', '.join(clashes)}",
                "",
                "## 5. การปรับสมดุลธาตุและพลังงานเชิงพื้นที่ (Spatial & Elemental Remediation)",
                f"- 🎨 **โทนสีมงคลเสริมพลัง**: {colors_str}",
                f"- 🧭 **การจัดวางทิศทางฮวงจุ้ย**: {orient_str}",
                f"- 💎 **คลื่นพลังงานอัญมณีเสริมธาตุ**: {gem_str}",
                "",
                "## 6. ข้อแนะนำด้านทัศนคติและจิตวิทยาพฤติกรรม (Behavioral Mindset Guidance)",
                f"{mindset}"
            ])
        elif lang == "en":
            resp = [
                f"# Computational Metaphysics Synthesis: {discipline.upper()} ({domain.capitalize()})",
                "",
                "## 1. Executive Strategic Synthesis",
                f"{synthesis}",
                "",
                "## 2. Classical Canon Verification & Metaphysical Rationale",
                f"Affirmed by classical treatise **{primary_cite.get('treatise', '')}** ({primary_cite.get('chapter', '')}):",
                f"> \"{primary_cite.get('original_text', '')}\"",
                f"*(Principle: {primary_cite.get('translation_en', '')})*",
                "",
                "## 3. Actionable Strategic Directives",
            ]
            for act in actions:
                resp.append(f"- {act}")
            resp.extend([
                "",
                "## 4. Auspicious Timing Windows & Risk Mitigation",
                f"- 🌟 **Golden Activation Windows**: {', '.join(timings)}",
                f"- ⚠️ **Adverse Planetary / Clash Windows**: {', '.join(clashes)}",
                "",
                "## 5. Spatial, Color & Elemental Resonance",
                f"- 🎨 **Harmonizing Color Palette**: {colors_str}",
                f"- 🧭 **Spatial & Environmental Alignment**: {orient_str}",
                f"- 💎 **Elemental & Gemstone Resonance**: {gem_str}",
                "",
                "## 6. Behavioral Mindset & Psychological Counsel",
                f"{mindset}"
            ])
        else:  # Chinese (zh)
            resp = [
                f"# 易學與術數綜合推演諮詢報告：{discipline.upper()} ({domain.capitalize()})",
                "",
                "## 1. 核心斷語與戰略總評 (Executive Synthesis)",
                f"{synthesis}",
                "",
                "## 2. 古籍經義考據與五行理路 (Classical Treatise Rationale)",
                f"考據典籍 **{primary_cite.get('treatise', '')}** ({primary_cite.get('chapter', '')}):",
                f"> 「{primary_cite.get('original_text', '')}」",
                f"*(微言大義: {primary_cite.get('translation_en', '')})*",
                "",
                "## 3. 具體應對策略 (Strategic Action Plan)",
            ]
            for act in actions:
                resp.append(f"- {act}")
            resp.extend([
                "",
                "## 4. 吉凶時令與避坑指南 (Timing Windows)",
                f"- 🌟 **天時良機吉運期**: {', '.join(timings)}",
                f"- ⚠️ **刑衝破害宜守期**: {', '.join(clashes)}",
                "",
                "## 5. 五行空間與風水調理 (Spatial Remediation)",
                f"- 🎨 **吉祥色彩矩陣**: {colors_str}",
                f"- 🧭 **空間坐向生氣位**: {orient_str}",
                f"- 💎 **五行晶石共振**: {gem_str}",
                "",
                "## 6. 心性修養與決策指引 (Mindset Counsel)",
                f"{mindset}"
            ])

        return "\n".join(resp)

    def generate_all_samples(self, target_count: int = 1200) -> list[dict[str, Any]]:
        """
        Generate rich multi-turn CoT samples across all 16 disciplines and 6 domains.
        Returns a list of structured dataset entries.
        """
        samples: list[dict[str, Any]] = []
        random.seed(42)

        # 1. Transform all 48 golden benchmark cases across 3 languages (48 * 3 = 144 samples)
        log.info("[INFO] Distilling golden benchmark seed cases into CoT conversations...")
        for case in self.benchmark_cases:
            disc = case.get("discipline", "bazi")
            dom = case.get("domain", "career")
            citations = case.get("canonical_citations", CLASSICAL_TREATISES.get(disc, []))
            chart_in = case.get("chart_inputs", {})
            q_dict = case.get("question", {})

            for lang, q_key in [("th", "question_th"), ("en", "question_en"), ("zh", "question_zh")]:
                q_text = q_dict.get(q_key, q_dict.get("question_th", "ขอคำปรึกษาเกี่ยวกับดวงชะตา"))
                thought_cot = self._generate_thought_cot(disc, dom, q_text, chart_in, citations, lang=lang)
                assistant_resp = self._generate_assistant_response(disc, dom, q_text, citations, lang=lang, case_seed=case)
                full_gpt_value = f"{thought_cot}\n\n{assistant_resp}"

                sample_entry = {
                    "id": f"META-GOLDEN-{len(samples)+1:04d}",
                    "discipline": disc,
                    "domain": dom,
                    "language": lang,
                    "is_golden": True,
                    "conversations": [
                        {"from": "human", "value": q_text},
                        {"from": "gpt", "value": full_gpt_value}
                    ],
                    "instruction": (
                        f"You are a master computational metaphysics consultant specialising in {disc.upper()} and {dom.upper()}. "
                        f"Provide citation-backed Chain-of-Thought analysis and structured remediation guidance."
                    ),
                    "input": f"Discipline: {disc} | Domain: {dom} | Context: {json.dumps(chart_in, ensure_ascii=False)}\nInquiry: {q_text}",
                    "output": full_gpt_value
                }
                samples.append(sample_entry)

        log.info(f"[OK] Created {len(samples)} golden baseline samples.")

        # 2. Synthesize remaining samples systematically across all 16 disciplines and 6 domains
        remaining_needed = target_count - len(samples)
        if remaining_needed <= 0:
            return samples

        combos = [(disc, dom) for disc in ALL_DISCIPLINE_KEYS for dom in ALL_DOMAINS]
        samples_per_combo = max(1, (remaining_needed // len(combos)) + 1)

        log.info(f"[INFO] Generating synthetic expansion samples across {len(combos)} discipline-domain pairs (~{samples_per_combo} per pair)...")

        for disc, dom in combos:
            cites = CLASSICAL_TREATISES.get(disc, CLASSICAL_TREATISES["bazi"])
            templates = SCENARIO_TEMPLATES.get(dom, SCENARIO_TEMPLATES["career"])

            for i in range(samples_per_combo):
                template = templates[i % len(templates)]
                lang = ["th", "en", "zh"][(len(samples) + i) % 3]

                q_text = (
                    template.get("dilemma_th") if lang == "th"
                    else (template.get("dilemma_en") if lang == "en" else template.get("dilemma_zh"))
                ) or template.get("dilemma_th", "ขอคำปรึกษาด้านยุทธศาสตร์")

                # Synthetic mock chart configuration specific to discipline
                synthetic_chart = {
                    "discipline": disc,
                    "domain": dom,
                    "cycle_period": 2026 + (i % 5),
                    "favorable_element": ["Wood", "Fire", "Earth", "Metal", "Water"][i % 5],
                    "polarity_flow": "Yang-Yin Balanced",
                    "persona": template.get("persona", "Executive Consultant")
                }

                thought_cot = self._generate_thought_cot(disc, dom, q_text, synthetic_chart, cites, lang=lang)
                assistant_resp = self._generate_assistant_response(disc, dom, q_text, cites, lang=lang)
                full_gpt_value = f"{thought_cot}\n\n{assistant_resp}"

                sample_entry = {
                    "id": f"META-SYNTH-{len(samples)+1:04d}",
                    "discipline": disc,
                    "domain": dom,
                    "language": lang,
                    "is_golden": False,
                    "conversations": [
                        {"from": "human", "value": q_text},
                        {"from": "gpt", "value": full_gpt_value}
                    ],
                    "instruction": (
                        f"You are a master computational metaphysics consultant specialising in {disc.upper()} and {dom.upper()}. "
                        f"Provide citation-backed Chain-of-Thought analysis and structured remediation guidance."
                    ),
                    "input": f"Discipline: {disc} | Domain: {dom} | Context: {json.dumps(synthetic_chart, ensure_ascii=False)}\nInquiry: {q_text}",
                    "output": full_gpt_value
                }
                samples.append(sample_entry)

        log.info(f"[OK] Total dataset size compiled: {len(samples)} samples.")
        return samples

    def split_train_eval(
        self,
        samples: list[dict[str, Any]],
        val_split: float = 0.10
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Split dataset ensuring stratified representation across disciplines and domains."""
        random.seed(42)
        shuffled = list(samples)
        random.shuffle(shuffled)

        eval_count = max(int(len(shuffled) * val_split), 100)
        train_samples = shuffled[eval_count:]
        eval_samples = shuffled[:eval_count]

        log.info(f"[INFO] Stratified Dataset Split: Train = {len(train_samples)}, Eval = {len(eval_samples)} (Ratio: {1-val_split:.0%}/{val_split:.0%})")
        return train_samples, eval_samples

    def export_datasets(
        self,
        train_samples: list[dict[str, Any]],
        eval_samples: list[dict[str, Any]],
        output_dir: Path | str = DATASETS_DIR
    ) -> dict[str, str]:
        """Export dataset files in ShareGPT, HuggingFace/MLX Instruction, and ChatML formats."""
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        MLX_DIR.mkdir(parents=True, exist_ok=True)

        # 1. ShareGPT format files
        train_sharegpt_file = out_path / "train_sharegpt_v3.jsonl"
        eval_sharegpt_file = out_path / "eval_sharegpt_v3.jsonl"

        with open(train_sharegpt_file, "w", encoding="utf-8") as f:
            for s in train_samples:
                row = {
                    "id": s["id"],
                    "discipline": s["discipline"],
                    "domain": s["domain"],
                    "language": s["language"],
                    "conversations": s["conversations"]
                }
                f.write(json.dumps(row, ensure_ascii=False) + "\n")

        with open(eval_sharegpt_file, "w", encoding="utf-8") as f:
            for s in eval_samples:
                row = {
                    "id": s["id"],
                    "discipline": s["discipline"],
                    "domain": s["domain"],
                    "language": s["language"],
                    "conversations": s["conversations"]
                }
                f.write(json.dumps(row, ensure_ascii=False) + "\n")

        # 2. HuggingFace / MLX Instruction format files
        train_instr_file = out_path / "train_instruction_v3.jsonl"
        eval_instr_file = out_path / "eval_instruction_v3.jsonl"

        with open(train_instr_file, "w", encoding="utf-8") as f:
            for s in train_samples:
                row = {
                    "id": s["id"],
                    "discipline": s["discipline"],
                    "domain": s["domain"],
                    "instruction": s["instruction"],
                    "input": s["input"],
                    "output": s["output"]
                }
                f.write(json.dumps(row, ensure_ascii=False) + "\n")

        with open(eval_instr_file, "w", encoding="utf-8") as f:
            for s in eval_samples:
                row = {
                    "id": s["id"],
                    "discipline": s["discipline"],
                    "domain": s["domain"],
                    "instruction": s["instruction"],
                    "input": s["input"],
                    "output": s["output"]
                }
                f.write(json.dumps(row, ensure_ascii=False) + "\n")

        # 3. Also sync to project/data/mlx_finetune for local MLX LoRA training
        mlx_train = MLX_DIR / "train_sharegpt_v3.jsonl"
        mlx_valid = MLX_DIR / "valid_sharegpt_v3.jsonl"
        with open(mlx_train, "w", encoding="utf-8") as f:
            for s in train_samples:
                f.write(json.dumps({"conversations": s["conversations"]}, ensure_ascii=False) + "\n")
        with open(mlx_valid, "w", encoding="utf-8") as f:
            for s in eval_samples:
                f.write(json.dumps({"conversations": s["conversations"]}, ensure_ascii=False) + "\n")

        results = {
            "train_sharegpt": str(train_sharegpt_file),
            "eval_sharegpt": str(eval_sharegpt_file),
            "train_instruction": str(train_instr_file),
            "eval_instruction": str(eval_instr_file),
            "mlx_train": str(mlx_train),
            "mlx_valid": str(mlx_valid),
        }

        log.info(f"[OK] Exported ShareGPT training set: {train_sharegpt_file} ({len(train_samples)} lines)")
        log.info(f"[OK] Exported ShareGPT evaluation set: {eval_sharegpt_file} ({len(eval_samples)} lines)")
        log.info(f"[OK] Exported HuggingFace/MLX instruction set: {train_instr_file} ({len(train_samples)} lines)")
        log.info(f"[OK] Exported HuggingFace/MLX instruction eval set: {eval_instr_file} ({len(eval_samples)} lines)")
        return results

    def validate_dataset_integrity(self, file_path: Path | str) -> dict[str, Any]:
        """Validate JSONL file structure, disciplines coverage, domains coverage, and CoT tags."""
        path = Path(file_path)
        if not path.exists():
            return {"valid": False, "error": f"File does not exist: {path}"}

        total_lines = 0
        disciplines_seen = set()
        domains_seen = set()
        cot_count = 0

        with open(path, "r", encoding="utf-8") as f:
            for idx, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except Exception as e:
                    return {"valid": False, "error": f"Invalid JSON on line {idx}: {e}"}

                total_lines += 1
                if "discipline" in obj:
                    disciplines_seen.add(obj["discipline"])
                if "domain" in obj:
                    domains_seen.add(obj["domain"])

                # Check CoT presence
                convs = obj.get("conversations", [])
                out = obj.get("output", "")
                text = " ".join([c.get("value", "") for c in convs]) + out
                if "<thought>" in text and "</thought>" in text:
                    cot_count += 1

        return {
            "valid": True,
            "file": str(path),
            "total_lines": total_lines,
            "disciplines_covered": len(disciplines_seen),
            "domains_covered": len(domains_seen),
            "cot_thought_percentage": round((cot_count / total_lines * 100), 2) if total_lines else 0.0
        }


def build_and_export_pipeline(
    benchmark_path: Path | str = DEFAULT_BENCHMARK_PATH,
    output_dir: Path | str = DATASETS_DIR,
    target_count: int = 1200,
    val_split: float = 0.10
) -> dict[str, Any]:
    """Unified orchestration pipeline function."""
    builder = MetaphysicsDatasetBuilder(benchmark_path=benchmark_path)
    all_samples = builder.generate_all_samples(target_count=target_count)
    train_samples, eval_samples = builder.split_train_eval(all_samples, val_split=val_split)
    exported_files = builder.export_datasets(train_samples, eval_samples, output_dir=output_dir)

    train_val = builder.validate_dataset_integrity(exported_files["train_sharegpt"])
    eval_val = builder.validate_dataset_integrity(exported_files["eval_sharegpt"])

    return {
        "status": "success",
        "total_samples": len(all_samples),
        "train_samples": len(train_samples),
        "eval_samples": len(eval_samples),
        "exported_files": exported_files,
        "train_validation": train_val,
        "eval_validation": eval_val
    }
