/**
 * HoroConsultant — Client-side Internationalization (i18n) Engine
 * Supports: Thai ('th'), English ('en'), Chinese ('zh')
 */

const I18N_STORAGE_KEY = 'horo_lang';
const DEFAULT_LOCALE = 'th';

const I18N_DICTIONARY = {
  th: {
    app_title: "HoroConsultant",
    tagline: "Computational Metaphysics & Multi-Agent Intelligence",
    nav_bazi: "🔮 BaZi Dashboard",
    nav_admin: "🔐 Admin Panel",
    
    // Form & Controls
    calc_chart_title: "🔮 คำนวณผังดวงชะตา (Calculate Chart)",
    calc_chart_desc: "ระบุเวลาเกิดและพิกัดลองจิจูดเพื่อปรับคำนวณเวลาสุริยคติจริง (True Solar Time)",
    user_name_label: "ชื่อ-นามสกุล (ไม่ระบุก็ได้ / Optional)",
    user_name_placeholder: "เช่น สมชาย ใจดี หรือเว้นว่างไว้",
    gender_label: "เพศกำเนิด (Gender at Birth)",
    gender_hint: "*กำหนดทิศทางวัยจร Da Yun",
    gender_male: "ชาย (Male)",
    gender_female: "หญิง (Female)",
    birth_datetime_label: "📅 วัน-เวลาเกิด Local Time (YYYY-MM-DD HH:MM:SS)",
    be_year_prefix: "พ.ศ. ",
    picker_placeholder: "แตะเพื่อเลือกวัน-เวลาเกิด (Drum Wheel Picker)",
    picker_btn: "📅 หมุนเลือกเวลา",
    unknown_hour: "🕒 ไม่ทราบเวลาเกิด (Unknown Time)",
    has_twin: "👥 เกิดเป็นฝาแฝด (Has Twin)",
    
    adv_settings_toggle: "⚙️ การตั้งค่าขั้นสูง (พิกัดเกิด & เวลาสุริยคติแท้ True Solar Time)",
    birth_location_label: "สถานที่เกิด (ค้นหาอำเภอ/จังหวัด/เมือง)",
    birth_location_placeholder: "พิมพ์ชื่อเมือง/จังหวัด เช่น เชียงใหม่, ขอนแก่น, โตเกียว...",
    preset_cities_label: "เลือกเมืองยอดนิยม (Quick Presets):",
    latitude_label: "ละติจูด (Latitude N):",
    longitude_label: "ลองจิจูด (Longitude E):",
    timezone_label: "เขตเวลา (Timezone Offset):",
    solar_mode_label: "โหมดเวลาสุริยคติแท้ (True Solar Time Mode):",
    solar_mode_tst: "เปิดใช้งาน True Solar Time (คำนวณตามองศาจริง + สมการเวลา)",
    solar_mode_local: "ใช้เวลาตามนาฬิกาท้องถิ่น (Local Standard Time)",
    
    btn_calculate_all: "🔮 คำนวณผังดวง 16 ศาสตร์ (Calculate All)",
    btn_interpret_ai: "✨ วิเคราะห์ดวงชะตาด้วย AI (AI Interpretation)",
    btn_export_report: "📄 ส่งออกรายงาน (Export Report)",
    report_title: "HoroConsultant — รายงานผลการคำนวณและวิเคราะห์ดวงชะตา",
    sky_clock_label: "🌌 ผังดาวจรท้องฟ้าเรียลไทม์ (Live Sky)",
    timeline_title: "⏳ แถบเลื่อนกาลเวลาวัยจร 10 ปี / ปีจร (DaYun & LiuNian Timeline Scrubber)",
    timeline_age_label: "เลือกช่วงอายุ:",
    btn_voice_input: "🎤 สั่งการด้วยเสียง",
    btn_listen_reading: "🔊 ฟังเสียง AI (Listen)",
    voice_reading_status: "กำลังอ่านบทพยากรณ์เสียง AI...",
    query_label: "คำถามหรือประเด็นที่ต้องการเน้น",
    synastry_mode_title: "โหมดวิเคราะห์ดวงสมพงษ์ 2 บุคคล (Synastry Mode)",
    synastry_mode_desc: "เปรียบเทียบดวงชะตาคู่รัก หรือพาร์ทเนอร์ธุรกิจ",
    partner_b_title: "👤 ข้อมูลบุคคลที่ 2 (Partner B)",
    partner_b_name_label: "ชื่อ/ฉายา Partner B",
    partner_b_datetime_label: "วันเวลาเกิด Partner B (YYYY-MM-DD HH:MM:SS)",
    synastry_result_title: "💖 ผลการวิเคราะห์ดวงสมพงษ์ & ธาตุคู่ครอง (Synastry Matrix)",
    calendar_title: "📅 ปฏิทินหมื่นปีฤกษ์มงคล 12 เทพ (Auspicious Calendar)",
    intent_all: "🌟 ทั้งหมด",
    intent_business: "💼 เปิดร้าน/ธุรกิจ",
    intent_marriage: "💍 แต่งงาน/หมั้น",
    intent_moving: "🏡 ย้ายบ้าน",
    intent_contract: "✍️ เซ็นสัญญา",
    luopan_title: "🧭 เข็มทิศหล่อแก 24 ขุนเขา & ผังพลังงาน 9 ยุค (24-Mountain LuoPan)",
    luopan_slider_label: "หมุนปรับองศาทิศหน้าบ้าน/อาคาร (Facing Degree):",
    dream_title: "🌙 ทำนายฝัน & ถอดรหัสสัญลักษณ์เทพ 64 ลักษณ์ (Dream Decoder)",
    dream_input_label: "พิมพ์รายละเอียดความฝัน หรือสัญลักษณ์ที่พบในฝัน:",
    btn_interpret_dream: "🔮 ทำนายฝัน",
    sim_title: "🔮 จำลองฉากทัศน์ชีวิตคู่ขนาน & วิเคราะห์ทางเลือก (What-If Life Path Simulator)",
    sim_desc: "จำลองเปรียบเทียบผลลัพธ์ทางเลือกสำคัญในชีวิต (การงาน/ธุรกิจ/ย้ายถิ่น) ผ่านการผสานธาตุประจำปีและพลังดาวจร 3-5 ปีข้างหน้า",
    btn_run_sim: "⚡ จำลองฉากทัศน์คู่ขนาน",
    btn_reset: "🔄 รีเซ็ตข้อมูล (Reset)",
    
    // 16 Disciplines Buttons
    disc_bazi: "四柱八字 (BaZi 4-Pillars)",
    disc_ziwei: "紫微斗數 (Zi Wei Dou Shu)",
    disc_qimen: "奇門遁甲 (Qi Men Dun Jia)",
    disc_liuren: "大六壬 (Da Liu Ren)",
    disc_iching: "易經六爻 (I Ching & Liu Yao)",
    disc_xuankong: "玄空風水 (Xuan Kong Flying Stars)",
    disc_zeji: "擇吉通書 (Ze Ji Timing)",
    disc_thai_vedic: "โหราศาสตร์ไทย (Thai Vedic)",
    disc_uranian: "ยูเรเนียน & สากล (Uranian)",
    disc_tai_yi: "太乙神數 (Tai Yi Shen Shu)",
    disc_liu_yao: "六爻預測 (Liu Yao Divination)",
    disc_meihua: "梅花易數 (Mei Hua Plum Blossom)",
    disc_sanhe: "三合風水 (San He Feng Shui)",
    disc_qizheng: "七政四餘 (Qi Zheng Si Yu)",
    disc_mianxiang: "麻衣神相 (Mian Xiang Face)",
    disc_satta_lek: "สัตตเลข 7 ฐาน & เลขศาสตร์",
    disc_multimodal: "ผังรวม 16 ศาสตร์ (Unified Matrix)",
    
    // Multimodal Matrix & Focus Domains
    matrix_title: "🌐 ผังรวมฉันทามติ 16 ศาสตร์ (Unified Multimodal Matrix)",
    matrix_subtitle: "วิเคราะห์ความสอดคล้องข้ามศาสตร์ตาม 6 มิติเป้าหมายชีวิต",
    consensus_index: "ดัชนีความสอดคล้อง (Consensus Score):",
    elemental_harmony: "ดุลยภาพเบญจธาตุ (Elemental Harmony):",
    auspicious_direction: "ทิศมงคลส่งเสริม (Auspicious Directions):",
    polarity_balance: "ขั้วพลังงาน (Polarity):",
    
    theme_career: "ธุรกิจการงาน (Career)",
    theme_finance: "การเงินโชคลาภ (Finance)",
    theme_love: "ความรักคู่ครอง (Love)",
    theme_health: "สุขภาพพลานามัย (Health)",
    theme_family: "ครอบครัวและที่อยู่อาศัย (Home)",
    theme_timing: "จังหวะชีวิตและกาลเวลา (Timing)",
    
    // Output Card Titles
    result_bazi_chart: "ผังดวงโป๊ยหยี่สี่เถียว (Four Pillars Chart)",
    result_day_master: "ดิถีประจำตัว (Day Master)",
    result_ming_gua: "รหัสราศีบุคคล (Ming Gua / Kua Number)",
    result_favorable_elements: "ธาตุที่ส่งเสริม (Favorable Elements)",
    result_structures_radar: "เรดาร์โครงสร้าง 5 ธาตุ (5 Structures Spider Chart)",
    result_profiles_chart: "สัดส่วน 10 รูปแบบดวง (10 Profiles Chart)",
    result_da_yun_cycles: "ถนนชีวิตและวัยจร 10 ปี (12 Da Yun Cycles)",
    result_annual_matrix: "ตารางปีจรประจำวัยจร (Annual Luck Matrix)",
    result_symbolic_stars: "ดาวเทพและดาวมงคล (Symbolic & General Stars)",
    
    // AI Interpretation Section
    ai_report_title: "📑 ผลการวิเคราะห์ดวงชะตาเชิงสังเคราะห์ (AI Synthesis)",
    ai_report_prompt_label: "คำถามหรือหัวข้อเฉพาะที่ต้องการเน้น (Focus Query):",
    ai_report_placeholder: "เช่น การเปลี่ยนสายงานปีนี้, โอกาสการลงทุน, ความสัมพันธ์คู่ครอง...",
    ai_loading: "กำลังรวบรวมข้อมูลคำนวณและวิเคราะห์ผล...",
    ai_model_source: "AI Engine:",
    ai_latency: "เวลาประมวลผล:",
    
    // Chat Assistant
    chat_launcher: "💬 ปรึกษาซินแส AI",
    chat_title: "🔮 ซินแส AI ผู้ช่วยดวงชะตา",
    chat_sub: "Live Metaphysics Consultant • Grounded RAG",
    chat_privacy: "🔒 Privacy Mode: Client Ephemeral (ไม่บันทึกข้อมูลส่วนบุคคล)",

    // Footer & Status
    health_status: "สถานะระบบ:",
    ready_status: "พร้อมใช้งาน",
    footer_version: "เวอร์ชัน:",
    footer_copyright: "© 2026 HoroConsultant Engine. All Rights Reserved."
  },
  
  en: {
    app_title: "HoroConsultant",
    tagline: "Computational Metaphysics & Multi-Agent Intelligence",
    nav_bazi: "🔮 BaZi Dashboard",
    nav_admin: "🔐 Admin Panel",
    
    // Form & Controls
    calc_chart_title: "🔮 Calculate Destiny Chart",
    calc_chart_desc: "Enter birth datetime and longitude coordinates to calibrate True Solar Time (TST)",
    user_name_label: "Full Name (Optional)",
    user_name_placeholder: "e.g. John Doe or leave blank",
    gender_label: "Gender at Birth",
    gender_hint: "*Determines Da Yun Luck Pillar direction",
    gender_male: "Male (乾造)",
    gender_female: "Female (坤造)",
    birth_datetime_label: "📅 Local Birth Date & Time (YYYY-MM-DD HH:MM:SS)",
    be_year_prefix: "AD ",
    picker_placeholder: "Tap to select birth datetime (Drum Wheel Picker)",
    picker_btn: "📅 Select Datetime",
    unknown_hour: "🕒 Unknown Birth Time",
    has_twin: "👥 Has Twin",
    
    adv_settings_toggle: "⚙️ Advanced Settings (Coordinates & True Solar Time)",
    birth_location_label: "Birth Location (City / Province)",
    birth_location_placeholder: "Type city or province name, e.g. Bangkok, Tokyo, London...",
    preset_cities_label: "Popular City Presets:",
    latitude_label: "Latitude (N):",
    longitude_label: "Longitude (E):",
    timezone_label: "Timezone Offset:",
    solar_mode_label: "True Solar Time Calibration:",
    solar_mode_tst: "Enable True Solar Time (Astronomical equation of time + longitude)",
    solar_mode_local: "Use Local Standard Clock Time",
    
    btn_calculate_all: "🔮 Calculate All 16 Disciplines",
    btn_interpret_ai: "✨ AI Multi-Agent Interpretation",
    btn_export_report: "📄 Export Consultation Dossier (PDF/Print)",
    report_title: "HoroConsultant — Astrological Consultation Dossier",
    sky_clock_label: "🌌 Live Celestial Sky Transit",
    timeline_title: "⏳ Interactive DaYun & LiuNian Timeline Scrubber",
    timeline_age_label: "Select Age:",
    btn_voice_input: "🎤 Voice Dictate",
    btn_listen_reading: "🔊 Listen to AI",
    voice_reading_status: "Reading AI Consultation Aloud...",
    query_label: "Focus Query or Consultation Topic",
    synastry_mode_title: "Dual-Profile Synastry & Compatibility Mode",
    synastry_mode_desc: "Compare partner charts for romantic or business synergy",
    partner_b_title: "👤 Partner B Profile Information",
    partner_b_name_label: "Partner B Name/Alias",
    partner_b_datetime_label: "Partner B Birth Datetime (YYYY-MM-DD HH:MM:SS)",
    synastry_result_title: "💖 Dual-Profile Synastry & Element Alignment Matrix",
    calendar_title: "📅 Astrological Calendar & Auspicious Date Selector",
    intent_all: "🌟 All Days",
    intent_business: "💼 Business Opening",
    intent_marriage: "💍 Marriage/Wedding",
    intent_moving: "🏡 Home Moving",
    intent_contract: "✍️ Contract Signing",
    luopan_title: "🧭 24-Mountain LuoPan & Period 9 Energy Heatmap",
    luopan_slider_label: "Rotate Building Facing Degree (0° - 360°):",
    dream_title: "🌙 AI Dream Interpreter & 64 Hexagrams Symbolism Decoder",
    dream_input_label: "Type your dream description or symbols:",
    btn_interpret_dream: "🔮 Decode Dream",
    sim_title: "🔮 Life Path Multi-Scenario Simulation & What-If Analyzer",
    sim_desc: "Simulate and compare strategic life decisions (career, startup, relocation) across 3-5 year transit trajectories.",
    btn_run_sim: "⚡ Run What-If Simulation",
    btn_reset: "🔄 Reset Form",
    
    // 16 Disciplines Buttons
    disc_bazi: "BaZi Four Pillars (四柱八字)",
    disc_ziwei: "Zi Wei Dou Shu (紫微斗數)",
    disc_qimen: "Qi Men Dun Jia (奇門遁甲)",
    disc_liuren: "Da Liu Ren (大六壬)",
    disc_iching: "I Ching & Liu Yao (易經六爻)",
    disc_xuankong: "Xuan Kong Flying Stars (玄空)",
    disc_zeji: "Ze Ji Auspicious Timing (擇吉)",
    disc_thai_vedic: "Thai Vedic & Jyotish",
    disc_uranian: "Western & Uranian Astro",
    disc_tai_yi: "Tai Yi Shen Shu (太乙神數)",
    disc_liu_yao: "Liu Yao 6-Lines (六爻預測)",
    disc_meihua: "Mei Hua Plum Blossom (梅花)",
    disc_sanhe: "San He 24-Mountains (三合)",
    disc_qizheng: "Qi Zheng Si Yu (七政四餘)",
    disc_mianxiang: "Mian Xiang Face Reading (面相)",
    disc_satta_lek: "Satta-Lek 7-Base Numerology",
    disc_multimodal: "Unified 16-Discipline Matrix",
    
    // Multimodal Matrix & Focus Domains
    matrix_title: "🌐 Unified 16-Discipline Consensus Matrix",
    matrix_subtitle: "Cross-Disciplinary Metaphysical Synthesis across 6 Life Domains",
    consensus_index: "Consensus Agreement Score:",
    elemental_harmony: "Five Elements Harmony:",
    auspicious_direction: "Auspicious Directions:",
    polarity_balance: "Polarity Dynamic:",
    
    theme_career: "Career & Business",
    theme_finance: "Wealth & Fortune",
    theme_love: "Love & Marriage",
    theme_health: "Health & Vitality",
    theme_family: "Family & Residence",
    theme_timing: "Timing & Luck Cycles",
    
    // Output Card Titles
    result_bazi_chart: "Four Pillars of Destiny Chart",
    result_day_master: "Day Master (Self Element)",
    result_ming_gua: "Personal Kua Number (Ming Gua)",
    result_favorable_elements: "Favorable Elements (Useful Gods)",
    result_structures_radar: "Five Structures Radar Chart",
    result_profiles_chart: "Ten Profiles Distribution",
    result_da_yun_cycles: "10-Year Major Luck Cycles (Da Yun)",
    result_annual_matrix: "Annual Luck Flow Matrix",
    result_symbolic_stars: "Symbolic & General Auxiliary Stars",
    
    // AI Interpretation Section
    ai_report_title: "📑 Synthetic Metaphysics Report (AI Synthesis)",
    ai_report_prompt_label: "Specific Question or Focus Query:",
    ai_report_placeholder: "e.g. Career transition timing, investment opportunity, relationship advice...",
    ai_loading: "Synthesizing classical rules and running inference...",
    ai_model_source: "AI Engine:",
    ai_latency: "Inference Latency:",
    
    // Chat Assistant
    chat_launcher: "💬 Consult AI Sin-Sae",
    chat_title: "🔮 Metaphysics AI Live Consultant",
    chat_sub: "Live Metaphysics Consultant • Grounded RAG",
    chat_privacy: "🔒 Privacy Mode: Client Ephemeral (No PII Stored)",

    // Footer & Status
    health_status: "System Health:",
    ready_status: "Operational",
    footer_version: "Version:",
    footer_copyright: "© 2026 HoroConsultant Engine. All Rights Reserved."
  },
  
  zh: {
    app_title: "HoroConsultant",
    tagline: "計算東方命理與多智能體綜合研判大腦",
    nav_bazi: "🔮 八字排盤與大盤",
    nav_admin: "🔐 管理後台",
    
    // Form & Controls
    calc_chart_title: "🔮 命盤排盤計算 (Calculate Chart)",
    calc_chart_desc: "輸入出生公曆時間與地理經度以精確校準真太陽時 (True Solar Time)",
    user_name_label: "姓名 (可選 / Optional)",
    user_name_placeholder: "例如：張三 或留空",
    gender_label: "出生性別 (Gender at Birth)",
    gender_hint: "*決定大運順逆排法",
    gender_male: "乾造 (男命 Male)",
    gender_female: "坤造 (女命 Female)",
    birth_datetime_label: "📅 當地出生年月日時 (YYYY-MM-DD HH:MM:SS)",
    be_year_prefix: "西元 ",
    picker_placeholder: "點擊選擇出生年月日時 (滾輪選擇器)",
    picker_btn: "📅 選擇時間",
    unknown_hour: "🕒 生辰未知 (Unknown Time)",
    has_twin: "👥 雙胞胎 (Has Twin)",
    
    adv_settings_toggle: "⚙️ 高級設定 (出生經緯度與真太陽時校準)",
    birth_location_label: "出生地點 (城市/省份/地區)",
    birth_location_placeholder: "輸入城市名稱，例如：北京、台北、曼谷、香港...",
    preset_cities_label: "常用城市預設:",
    latitude_label: "緯度 (Latitude N):",
    longitude_label: "經度 (Longitude E):",
    timezone_label: "時區偏移 (Timezone Offset):",
    solar_mode_label: "真太陽時模式 (True Solar Time):",
    solar_mode_tst: "啟用真太陽時校準 (結合天文時差方程與經度平移)",
    solar_mode_local: "使用鐘錶標準時間 (Local Clock Time)",
    
    btn_calculate_all: "🔮 排盤並計算16門術數 (Calculate All)",
    btn_interpret_ai: "✨ AI 智能多智能體深度詳批",
    btn_export_report: "📄 導出命理諮詢報告 (PDF/列印)",
    report_title: "HoroConsultant — 術數命理綜合諮詢報告書",
    sky_clock_label: "🌌 即時四柱天象鐘 (Live Sky)",
    timeline_title: "⏳ 大運流年互動時間軸滑塊 (Timeline Scrubber)",
    timeline_age_label: "選擇年齡/流年:",
    btn_voice_input: "🎤 語音輸入指令",
    btn_listen_reading: "🔊 語音朗讀詳批",
    voice_reading_status: "正在進行 AI 命理語音朗讀...",
    query_label: "諮詢問題或重點分析方向",
    synastry_mode_title: "雙人八字合婚與合夥配對模式 (Synastry Mode)",
    synastry_mode_desc: "深入分析雙方日主生剋、夫妻宮六合/相沖及五行互補",
    partner_b_title: "👤 第二位對象資料 (Partner B)",
    partner_b_name_label: "姓名/暱稱 Partner B",
    partner_b_datetime_label: "出生生辰 (YYYY-MM-DD HH:MM:SS)",
    synastry_result_title: "💖 雙人命理合盤與五行契合度分析報告 (Synastry Matrix)",
    calendar_title: "📅 擇吉萬年曆與建除十二神每日吉凶 (Auspicious Calendar)",
    intent_all: "🌟 全部吉凶",
    intent_business: "💼 開市/開業",
    intent_marriage: "💍 嫁娶/訂盟",
    intent_moving: "🏡 入宅/搬遷",
    intent_contract: "✍️ 簽約/交易",
    luopan_title: "🧭 二十四山專業羅盤與九運九宮飛星能量圖 (24-Mountain LuoPan)",
    luopan_slider_label: "旋轉設定建築座向度數 (0° - 360°):",
    dream_title: "🌙 吠陀周易釋夢與六十四卦象徵解碼 (Dream Decoder)",
    dream_input_label: "請輸入夢境描述或出現的特定象徵物:",
    btn_interpret_dream: "🔮 解碼夢境",
    sim_title: "🔮 多場景命理決策模擬與平行人生路徑分析 (What-If Simulator)",
    sim_desc: "基於未來3-5年流年五行氣運，全方位模擬對比事業轉型、創業投資與跨國發展之決策路徑。",
    btn_run_sim: "⚡ 運行多路徑決策模擬",
    btn_reset: "🔄 重置表單 (Reset)",
    
    // 16 Disciplines Buttons
    disc_bazi: "四柱八字 (BaZi 4-Pillars)",
    disc_ziwei: "紫微斗數 (Zi Wei Dou Shu)",
    disc_qimen: "奇門遁甲 (Qi Men Dun Jia)",
    disc_liuren: "大六壬 (Da Liu Ren)",
    disc_iching: "易經六爻 (I Ching & Liu Yao)",
    disc_xuankong: "玄空風水九星 (Xuan Kong)",
    disc_zeji: "擇吉通書 (Ze Ji Timing)",
    disc_thai_vedic: "泰國吠陀占星 (Thai Vedic)",
    disc_uranian: "西洋漢堡占星 (Uranian)",
    disc_tai_yi: "太乙神數 (Tai Yi Shen Shu)",
    disc_liu_yao: "六爻納甲預測 (Liu Yao)",
    disc_meihua: "梅花易數 (Mei Hua)",
    disc_sanhe: "三合水法二十四山 (San He)",
    disc_qizheng: "七政四餘天星 (Qi Zheng)",
    disc_mianxiang: "麻衣神相面相學 (Mian Xiang)",
    disc_satta_lek: "泰國七基數與迦勒底數字學",
    disc_multimodal: "16門術數全息大一統羅盤",
    
    // Multimodal Matrix & Focus Domains
    matrix_title: "🌐 16門術數大一統全息羅盤 (Multimodal Matrix)",
    matrix_subtitle: "融合東方星宿、三式絕學、形氣風水與相術之六大命運主題共識",
    consensus_index: "各派共識度 (Consensus Score):",
    elemental_harmony: "五行生剋平衡度 (Elemental Harmony):",
    auspicious_direction: "大吉開運方位 (Auspicious Directions):",
    polarity_balance: "陰陽二極流動 (Polarity):",
    
    theme_career: "事業功名 (Career)",
    theme_finance: "財運正偏財 (Finance)",
    theme_love: "感情婚姻 (Love)",
    theme_health: "身體健康 (Health)",
    theme_family: "六親家宅 (Home)",
    theme_timing: "流年運勢 (Timing)",
    
    // Output Card Titles
    result_bazi_chart: "八字命盤四柱總覽 (Four Pillars)",
    result_day_master: "日元日主本命 (Day Master)",
    result_ming_gua: "本命卦數 (Ming Gua)",
    result_favorable_elements: "喜用神與喜忌五行 (Favorable Elements)",
    result_structures_radar: "五格局雷達蜘蛛圖 (5 Structures Radar)",
    result_profiles_chart: "十神主導星分佈 (10 Profiles Chart)",
    result_da_yun_cycles: "十年大運與行運軌跡 (12 Da Yun Cycles)",
    result_annual_matrix: "流年流月交會矩陣 (Annual Matrix)",
    result_symbolic_stars: "神煞吉凶星曜 (Symbolic Stars)",
    
    // AI Interpretation Section
    ai_report_title: "📑 命理大腦綜合詳批報告 (AI Synthesis Report)",
    ai_report_prompt_label: "特定諮詢問題或重點方向 (Focus Query):",
    ai_report_placeholder: "例如：今年跳槽轉職吉凶、投資偏財運勢、近期婚姻感情指引...",
    ai_loading: "正在匯總古籍經典並調用模型進行深度研判...",
    ai_model_source: "分析引擎:",
    ai_latency: "研判耗時:",
    
    // Chat Assistant
    chat_launcher: "💬 諮詢 AI 命理師",
    chat_title: "🔮 AI 命理大師顧問",
    chat_sub: "Live Metaphysics Consultant • Grounded RAG",
    chat_privacy: "🔒 隱私安全模式：Client Ephemeral (不保存個人隱私記錄)",

    // Footer & Status
    health_status: "系統狀態:",
    ready_status: "運行中",
    footer_version: "版本號:",
    footer_copyright: "© 2026 HoroConsultant Engine. 版權所有."
  }
};

let currentLanguage = DEFAULT_LOCALE;

/**
 * Get current active language
 */
function getLanguage() {
  return currentLanguage;
}

/**
 * Translate a key with optional fallback
 */
function t(key, defaultVal = '') {
  const dict = I18N_DICTIONARY[currentLanguage] || I18N_DICTIONARY[DEFAULT_LOCALE];
  if (dict && dict[key]) {
    return dict[key];
  }
  const fallbackDict = I18N_DICTIONARY[DEFAULT_LOCALE];
  if (fallbackDict && fallbackDict[key]) {
    return fallbackDict[key];
  }
  return defaultVal || key;
}

/**
 * Apply translation across DOM elements with data-i18n attributes
 */
function applyI18nToDOM() {
  document.documentElement.lang = currentLanguage;
  
  // 1. Text elements with data-i18n
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.getAttribute('data-i18n');
    if (key) {
      const translated = t(key);
      if (translated) {
        el.innerText = translated;
      }
    }
  });

  // 2. Placeholder attributes with data-i18n-placeholder
  document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
    const key = el.getAttribute('data-i18n-placeholder');
    if (key) {
      const translated = t(key);
      if (translated) {
        el.setAttribute('placeholder', translated);
      }
    }
  });

  // 3. Update active state of language toggle buttons
  document.querySelectorAll('.lang-btn').forEach(btn => {
    const lang = btn.getAttribute('data-lang');
    if (lang === currentLanguage) {
      btn.classList.add('active');
    } else {
      btn.classList.remove('active');
    }
  });
}

/**
 * Switch language and persist to localStorage
 */
function setLanguage(lang) {
  if (!['th', 'en', 'zh'].includes(lang)) {
    lang = DEFAULT_LOCALE;
  }
  currentLanguage = lang;
  try {
    localStorage.setItem(I18N_STORAGE_KEY, lang);
  } catch (e) {
    console.warn('[i18n] localStorage write failed:', e);
  }
  applyI18nToDOM();
  
  // Dispatch custom event for dynamic components to re-render if needed
  window.dispatchEvent(new CustomEvent('horo-language-changed', { detail: { language: lang } }));
}

/**
 * Auto-detect browser locale or restore from localStorage
 */
function initI18n() {
  let savedLang = null;
  try {
    savedLang = localStorage.getItem(I18N_STORAGE_KEY);
  } catch (e) {}

  if (savedLang && ['th', 'en', 'zh'].includes(savedLang)) {
    currentLanguage = savedLang;
  } else {
    // Detect from browser navigator.language
    const browserLang = (navigator.language || navigator.userLanguage || '').toLowerCase();
    if (browserLang.startsWith('zh')) {
      currentLanguage = 'zh';
    } else if (browserLang.startsWith('en')) {
      currentLanguage = 'en';
    } else {
      currentLanguage = 'th';
    }
  }

  applyI18nToDOM();
}

// Attach to global window
if (typeof window !== 'undefined') {
  window.t = t;
  window.getLanguage = getLanguage;
  window.setLanguage = setLanguage;
  window.initI18n = initI18n;
  window.I18N_DICTIONARY = I18N_DICTIONARY;
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    t,
    getLanguage,
    setLanguage,
    initI18n,
    I18N_DICTIONARY,
    DEFAULT_LOCALE
  };
}
