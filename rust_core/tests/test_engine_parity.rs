use rust_core::fengshui::{calculate_xuankong_chart_rust, resolve_mountain_rust};
use rust_core::iching::calculate_iching_chart_rust;
use rust_core::liuren::calculate_liuren_chart_rust;
use rust_core::numerology::{calculate_numerology_score_rust, calculate_satta_lek_chart_rust};
use rust_core::observability::MetricsRegistry;
use rust_core::qimen::calculate_qimen_chart_rust;
use rust_core::svg::{render_bazi_svg, render_qimen_svg, render_xuankong_svg, render_ziwei_svg};
use rust_core::thai_vedic::calculate_thai_vedic_chart_rust;
use rust_core::zeji::calculate_zeji_chart_rust;
use rust_core::ziwei::calculate_ziwei_chart_rust;
use serde_json::json;
use serde_json::Value;
use std::io::{BufRead, BufReader};
use std::process::{Command, Stdio};
use std::time::Instant;

#[test]
fn xuankong_mountain_indices_are_centred_on_all_24_mountains() {
    // A zero-based UI segment index denotes the 15-degree segment centered at
    // index * 15 degrees.  The old implementation treated it as an index into
    // a boundary-ordered table, shifting every result by one mountain.
    let expected = [
        "子", "癸", "丑", "艮", "寅", "甲", "卯", "乙", "辰", "巽", "巳", "丙", "午", "丁", "未",
        "坤", "申", "庚", "酉", "辛", "戌", "乾", "亥", "壬",
    ];

    let actual: Vec<_> = (0..24).map(resolve_mountain_rust).collect();
    assert_eq!(actual, expected);
}

#[test]
fn metrics_exposition_matches_literal_python_fallback_schema() {
    let mut registry = MetricsRegistry::default();
    registry.record_request("GET", "/health", 200, 0.125);
    registry.record_rag_search(0.042);
    registry.record_llm_inference("dummy", "success", 0.1);

    assert_eq!(
        registry.generate_metrics_text(12.34),
        concat!(
            "# HELP process_uptime_seconds Total application uptime in seconds\n",
            "# TYPE process_uptime_seconds gauge\n",
            "process_uptime_seconds 12.34\n\n",
            "# HELP http_requests_total Total count of HTTP requests\n",
            "# TYPE http_requests_total counter\n",
            "http_requests_total{method=\"GET\",endpoint=\"/health\",status_code=\"200\"} 1\n\n",
            "# HELP http_request_duration_seconds_count Total number of HTTP request duration observations\n",
            "# TYPE http_request_duration_seconds_count counter\n",
            "http_request_duration_seconds_count{method=\"GET\",endpoint=\"/health\"} 1\n\n",
            "# HELP http_request_duration_seconds_sum Total cumulative HTTP request duration\n",
            "# TYPE http_request_duration_seconds_sum counter\n",
            "http_request_duration_seconds_sum{method=\"GET\",endpoint=\"/health\"} 0.1250\n\n",
            "# HELP rag_search_total Total RAG vector store queries\n",
            "# TYPE rag_search_total counter\n",
            "rag_search_total 1\n\n",
            "# HELP rag_search_latency_seconds_sum Total RAG vector store retrieval duration\n",
            "# TYPE rag_search_latency_seconds_sum counter\n",
            "rag_search_latency_seconds_sum 0.0420\n",
            "llm_inference_total{provider=\"dummy\",status=\"success\"} 1\n",
        )
    );
}

#[test]
fn chaldean_numerology_matches_literal_python_schema() {
    let actual = calculate_numerology_score_rust("0812345678", "fixed");
    assert_eq!(
        actual,
        json!({
            "engine":"ChaldeanNumerologyEngine","input_text":"0812345678","total_score":44,
            "reduced_root_digit":8,
            "digit_meaning":"ราหู (8) - ความชาญฉลาด พลิกผัน โชคลาภกะทันหัน ความทะเยอทะยาน",
            "engine_name":"Numerology & Satta-Lek Engine","system_type":"numerology","calculation_timestamp":"fixed"
        })
    );
}

#[test]
fn chaldean_numerology_mixes_thai_letters_ascii_letters_and_digits() {
    let actual = calculate_numerology_score_rust("ดอ6ZF8BYฮมพ", "fixed");
    assert_eq!(actual["total_score"], 57);
    assert_eq!(actual["reduced_root_digit"], 3);
}

#[test]
fn satta_lek_chart_matches_literal_python_schema() {
    let actual = calculate_satta_lek_chart_rust(2, 6, 7, "fixed").unwrap();
    let expected = json!({
        "engine":"SattaLekEngine","day_num":2,"lunar_month":6,"year_zodiac_num":7,
        "matrix_7_base":[
            {"house_name":"อัตตา","row1_day":2,"row2_month":6,"row3_year":7,"row4_sum":15},
            {"house_name":"หินะ","row1_day":3,"row2_month":7,"row3_year":1,"row4_sum":11},
            {"house_name":"ธนัง","row1_day":4,"row2_month":1,"row3_year":2,"row4_sum":7},
            {"house_name":"ปิตา","row1_day":5,"row2_month":2,"row3_year":3,"row4_sum":10},
            {"house_name":"มาตา","row1_day":6,"row2_month":3,"row3_year":4,"row4_sum":13},
            {"house_name":"โภคา","row1_day":7,"row2_month":4,"row3_year":5,"row4_sum":16},
            {"house_name":"มัชฌิมา","row1_day":1,"row2_month":5,"row3_year":6,"row4_sum":12}
        ],
        "engine_name":"Numerology & Satta-Lek Engine","system_type":"numerology","calculation_timestamp":"fixed"
    });
    assert_eq!(actual, expected);
}

#[test]
fn zeji_chart_matches_literal_python_schema() {
    let actual = calculate_zeji_chart_rust("午", "申", "寅", Some("子"), "fixed").unwrap();
    let expected = json!({
        "engine":"ZeJiEngine","duty_officer":"破日",
        "duty_description":"衝破不和。宜破屋、壞垣、求醫；忌辦喜事、開張。",
        "rating_stars":1,"overall_status":"凶 - 大事不宜 (歲破/月破/破日)",
        "is_year_breaker":false,"is_month_breaker":true,"is_user_clash":false,
        "activities_suitability":{"結婚訂婚":"忌","開市開業":"忌","搬家入宅":"忌","出行遠遊":"忌","求醫治病":"宜"},
        "engine_name":"Imperial Calendar Date Selection Engine","system_type":"ze_ji","calculation_timestamp":"fixed"
    });
    assert_eq!(actual, expected);
}

#[test]
fn liuren_chart_matches_literal_python_schema() {
    let actual = calculate_liuren_chart_rust("甲", "子", "正月", "午", "fixed").unwrap();
    let expected = json!({
        "engine":"LiuRenEngine","day_stem_branch":"甲子","month_general":"正月 (亥)","hour_branch":"午",
        "heaven_plate":{"午":"亥","未":"子","申":"丑","酉":"寅","戌":"卯","亥":"辰","子":"巳","丑":"午","寅":"未","卯":"申","辰":"酉","巳":"戌"},
        "four_lessons":[
            {"lesson_name":"第一課 (干上)","bottom":"甲","top":"未"},
            {"lesson_name":"第二課 (干上上)","bottom":"未","top":"子"},
            {"lesson_name":"第三課 (支上)","bottom":"子","top":"巳"},
            {"lesson_name":"第四課 (支上上)","bottom":"巳","top":"戌"}
        ],
        "three_transmissions":{"初傳 (發端)":"未","中傳 (移革)":"子","末傳 (歸結)":"巳"},
        "generals_plate":{"亥":"貴人","子":"螣蛇","丑":"朱雀","寅":"六合","卯":"勾陳","辰":"青龍","巳":"天空","午":"白虎","未":"太常","申":"玄武","酉":"太陰","戌":"天后"},
        "engine_name":"Da Liu Ren Engine","system_type":"san_shi","calculation_timestamp":"fixed"
    });
    assert_eq!(actual, expected);
}

#[test]
fn iching_chart_matches_literal_python_schema() {
    let actual = calculate_iching_chart_rust("甲", &[6, 7, 8, 9, 7, 8], "fixed").unwrap();
    let expected = json!({
        "engine":"IChingEngine","day_stem":"甲","raw_lines":[6,7,8,9,7,8],
        "primary_hexagram":{"binary":"010110","name":"本卦","nature":"吉"},
        "transformed_hexagram":{"binary":"110010","name":"變卦"},
        "six_lines":[
            {"line_number":1,"line_value":6,"line_type":"陰爻","is_moving":true,"relative":"父母","animal":"青龍"},
            {"line_number":2,"line_value":7,"line_type":"陽爻","is_moving":false,"relative":"兄弟","animal":"朱雀"},
            {"line_number":3,"line_value":8,"line_type":"陰爻","is_moving":false,"relative":"子孫","animal":"勾陳"},
            {"line_number":4,"line_value":9,"line_type":"陽爻","is_moving":true,"relative":"妻財","animal":"騰蛇"},
            {"line_number":5,"line_value":7,"line_type":"陽爻","is_moving":false,"relative":"官鬼","animal":"白虎"},
            {"line_number":6,"line_value":8,"line_type":"陰爻","is_moving":false,"relative":"父母","animal":"玄武"}
        ],
        "engine_name":"I Ching & Liu Yao Engine","system_type":"pu_shi","calculation_timestamp":"fixed"
    });
    assert_eq!(actual, expected);
}

#[test]
fn thai_vedic_chart_matches_literal_python_schema() {
    let actual = calculate_thai_vedic_chart_rust(1990, 5, 15, 14, 2, "fixed");
    let expected = json!({
        "engine":"ThaiVedicEngine","datetime":"1990-05-15 14:00",
        "thai_lagna":"ราศีกันย์ (House 6)",
        "maha_thaksa":{
            "บริวาร":"อังคาร (3)","อายุ":"พุธ (4)","เดช":"เสาร์ (7)","ศรี":"พฤหัสบดี (5)",
            "มูละ":"ราหู (8)","อุตสาหะ":"ศุกร์ (6)","มนตรี":"อาทิตย์ (1)","กาลกิณี":"จันทร์ (2)"
        },
        "kalakini_planet":"จันทร์ (2)","sri_planet":"พฤหัสบดี (5)",
        "vedic_nakshatra":{"name":"อุตตรภัทรบท (Uttara Bhadrapada)","number":26,"pada":2,"moon_degree":338.76},
        "vimshottari_dasha":"มาฆะ (Ketu)",
        "engine_name":"Thai & Vedic Suriyayart Engine","system_type":"thai_vedic","calculation_timestamp":"fixed"
    });
    assert_eq!(actual, expected);
}

#[test]
fn qimen_chart_matches_literal_python_schema() {
    let actual = calculate_qimen_chart_rust(2026, 8, 7, 14, None, "fixed");
    let expected = json!({
        "engine":"QiMenEngine","datetime":"2026-08-07 14:00","solar_term":"立秋",
        "dun_type":"Yin","ju_number":5,
        "palaces":[
            {"palace_number":1,"earth_stem":"壬","star":"天蓬","door":"休門","spirit":"值符"},
            {"palace_number":2,"earth_stem":"辛","star":"天芮","door":"死門","spirit":"玄武"},
            {"palace_number":3,"earth_stem":"庚","star":"天衝","door":"傷門","spirit":"太陰"},
            {"palace_number":4,"earth_stem":"己","star":"天輔","door":"杜門","spirit":"六合"},
            {"palace_number":5,"earth_stem":"戊","star":"天禽","door":"生門","spirit":"值符"},
            {"palace_number":6,"earth_stem":"乙","star":"天心","door":"開門","spirit":"九天"},
            {"palace_number":7,"earth_stem":"丙","star":"天柱","door":"驚門","spirit":"九地"},
            {"palace_number":8,"earth_stem":"丁","star":"天任","door":"生門","spirit":"騰蛇"},
            {"palace_number":9,"earth_stem":"癸","star":"天英","door":"景門","spirit":"白虎"}
        ],
        "engine_name":"Qi Men Dun Jia Engine","system_type":"san_shi","calculation_timestamp":"fixed"
    });
    assert_eq!(actual, expected);
}

#[test]
fn ziwei_chart_matches_literal_python_schema() {
    let actual = calculate_ziwei_chart_rust(1990, 5, 15, 14, "male", "fixed");
    let expected = json!({
        "engine":"ZiWeiEngine","birth_solar":"1990-05-15 14:00","year_stem_branch":"庚午",
        "hour_branch":"未","ming_gong_branch":"亥","shen_gong_branch":"丑",
        "five_element_bureau":"土五局","zi_wei_star_branch":"辰","tian_fu_star_branch":"子",
        "si_hua":{"化祿":"太陽","化權":"武曲","化科":"太陰","化忌":"天同"},
        "palaces":[
            {"palace_name":"命宮","earth_branch":"亥","stars":["天同"],"mutators":["天同化忌"],"is_ming_gong":true,"is_shen_gong":false},
            {"palace_name":"兄弟宮","earth_branch":"戌","stars":["破軍"],"mutators":[],"is_ming_gong":false,"is_shen_gong":false},
            {"palace_name":"夫妻宮","earth_branch":"酉","stars":[],"mutators":[],"is_ming_gong":false,"is_shen_gong":false},
            {"palace_name":"子女宮","earth_branch":"申","stars":["廉貞"],"mutators":[],"is_ming_gong":false,"is_shen_gong":false},
            {"palace_name":"財帛宮","earth_branch":"未","stars":[],"mutators":[],"is_ming_gong":false,"is_shen_gong":false},
            {"palace_name":"疾厄宮","earth_branch":"午","stars":["七殺"],"mutators":[],"is_ming_gong":false,"is_shen_gong":false},
            {"palace_name":"遷移宮","earth_branch":"巳","stars":["天梁"],"mutators":[],"is_ming_gong":false,"is_shen_gong":false},
            {"palace_name":"交友宮","earth_branch":"辰","stars":["紫微","天相"],"mutators":[],"is_ming_gong":false,"is_shen_gong":false},
            {"palace_name":"官祿宮","earth_branch":"卯","stars":["天機","巨門"],"mutators":[],"is_ming_gong":false,"is_shen_gong":false},
            {"palace_name":"田宅宮","earth_branch":"寅","stars":["貪狼"],"mutators":[],"is_ming_gong":false,"is_shen_gong":false},
            {"palace_name":"福德宮","earth_branch":"丑","stars":["太陽","太陰"],"mutators":["太陽化祿","太陰化科"],"is_ming_gong":false,"is_shen_gong":true},
            {"palace_name":"父母宮","earth_branch":"子","stars":["武曲","天府"],"mutators":["武曲化權"],"is_ming_gong":false,"is_shen_gong":false}
        ],
        "engine_name":"Zi Wei Dou Shu Engine","system_type":"ming_xue","calculation_timestamp":"fixed"
    });
    assert_eq!(actual, expected);
}

#[test]
fn xuankong_svg_preserves_mountains_directions_and_three_stars() {
    let chart = json!({
        "period":9,"facing_degree":180.0,
        "facing_mountain":"午 (離卦 - 陰)","sitting_mountain":"子 (坎卦 - 陰)",
        "grid_palaces":[
            {"palace_number":1,"palace_name":"坎","direction":"北","base_star":5,"sitting_star":4,"facing_star":8},
            {"palace_number":9,"palace_name":"離","direction":"南","base_star":4,"sitting_star":5,"facing_star":9}
        ]
    });
    let svg = render_xuankong_svg(&chart, "ผังดวง玄空風水");
    for literal in [
        "ผังดวง玄空風水",
        "第 9 運",
        "午 (離卦 - 陰)",
        "子 (坎卦 - 陰)",
        "北 (坎)",
        "山星: 4",
        "向星: 8",
        "運星: 5",
        "南 (離)",
        "山星: 5",
        "向星: 9",
        "運星: 4",
    ] {
        assert!(
            svg.contains(literal),
            "missing literal SVG content: {literal}"
        );
    }
}

#[test]
fn qimen_svg_preserves_all_four_plate_values() {
    let chart = json!({
        "solar_term":"立秋","dun_type":"Yin","ju_number":5,
        "palaces":[
            {"palace_number":1,"earth_stem":"壬","star":"天蓬","door":"休門","spirit":"值符"},
            {"palace_number":9,"earth_stem":"癸","star":"天英","door":"景門","spirit":"白虎"}
        ]
    });
    let svg = render_qimen_svg(&chart, "ผังดวง奇門遁甲");
    for literal in [
        "ผังดวง奇門遁甲",
        "立秋",
        "Yin遁 5局",
        "宮位 1",
        "天蓬",
        "休門",
        "值符",
        "宮位 9",
        "天英",
        "景門",
        "白虎",
        "天干: 壬",
        "天干: 癸",
    ] {
        assert!(
            svg.contains(literal),
            "missing literal SVG content: {literal}"
        );
    }
}

#[test]
fn ziwei_svg_preserves_palace_stars_and_mutators() {
    let chart = json!({
        "five_element_bureau":"土五局",
        "ming_gong_branch":"亥",
        "shen_gong_branch":"丑",
        "palaces":[
            {"palace_name":"命宮","earth_branch":"亥","stars":["天同"],"mutators":["天同化忌"],"is_ming_gong":true,"is_shen_gong":false},
            {"palace_name":"父母宮","earth_branch":"子","stars":["武曲","天府"],"mutators":["武曲化權"],"is_ming_gong":false,"is_shen_gong":false}
        ]
    });

    let svg = render_ziwei_svg(&chart, "ผังดวง紫微斗數");
    for literal in [
        "ผังดวง紫微斗數",
        "土五局",
        "命宮 (亥)",
        "天同",
        "天同化忌",
        "父母宮 (子)",
        "武曲 天府",
        "武曲化權",
    ] {
        assert!(
            svg.contains(literal),
            "missing literal SVG content: {literal}"
        );
    }
}

#[test]
fn bazi_svg_preserves_literal_chart_content() {
    let chart = json!({
        "day_master": {"stem":"庚","element":"Metal","polarity":"Yang"},
        "solar_time_info": {"tst_datetime":"1990-05-15 14:09:13"},
        "five_elements": {"percentages": {
            "Wood": 12.5, "Fire": 17.5, "Earth": 20.0, "Metal": 30.0, "Water": 20.0
        }},
        "pillars": {
            "hour": {"stem":{"char":"癸","pinyin":"Guǐ","element":"Water"},"branch":{"char":"未","pinyin":"Wèi","animal":"Goat","element":"Earth"}},
            "day": {"stem":{"char":"庚","pinyin":"Gēng","element":"Metal"},"branch":{"char":"午","pinyin":"Wǔ","animal":"Horse","element":"Fire"}},
            "month": {"stem":{"char":"辛","pinyin":"Xīn","element":"Metal"},"branch":{"char":"巳","pinyin":"Sì","animal":"Snake","element":"Fire"}},
            "year": {"stem":{"char":"庚","pinyin":"Gēng","element":"Metal"},"branch":{"char":"午","pinyin":"Wǔ","animal":"Horse","element":"Fire"}}
        }
    });

    let svg = render_bazi_svg(&chart, "ผังดวงชะตา BaZi");
    for literal in [
        "ผังดวงชะตา BaZi",
        "1990-05-15 14:09:13",
        "庚",
        "Metal Yang",
        "癸",
        "Guǐ",
        "未",
        "Goat",
        "Wood: 12.5%",
        "Metal: 30.0%",
    ] {
        assert!(
            svg.contains(literal),
            "missing literal SVG content: {literal}"
        );
    }
    assert!(svg.starts_with("<svg"));
    assert!(svg.ends_with("</svg>"));
}

#[test]
fn xuankong_chart_matches_literal_python_schema() {
    let actual = calculate_xuankong_chart_rust(180.0, 9, "fixed");
    let expected = json!({
        "engine": "XuanKongEngine",
        "period": 9,
        "facing_degree": 180.0,
        "facing_mountain": "午 (離卦 - 陰)",
        "sitting_mountain": "子 (坎卦 - 陰)",
        "grid_palaces": [
            {"palace_number":1,"palace_name":"坎","direction":"北","base_star":5,"sitting_star":4,"facing_star":8,"facing_star_name":"八白左輔星 (土)"},
            {"palace_number":2,"palace_name":"坤","direction":"西南","base_star":6,"sitting_star":3,"facing_star":7,"facing_star_name":"七赤破軍星 (金)"},
            {"palace_number":3,"palace_name":"震","direction":"東","base_star":7,"sitting_star":2,"facing_star":6,"facing_star_name":"六白武曲星 (金)"},
            {"palace_number":4,"palace_name":"巽","direction":"東南","base_star":8,"sitting_star":1,"facing_star":5,"facing_star_name":"五黃廉貞星 (土)"},
            {"palace_number":5,"palace_name":"中宮","direction":"中央","base_star":9,"sitting_star":9,"facing_star":4,"facing_star_name":"四綠文曲星 (木)"},
            {"palace_number":6,"palace_name":"乾","direction":"西北","base_star":1,"sitting_star":8,"facing_star":3,"facing_star_name":"三碧祿存星 (木)"},
            {"palace_number":7,"palace_name":"兌","direction":"西","base_star":2,"sitting_star":7,"facing_star":2,"facing_star_name":"二黑巨門星 (土)"},
            {"palace_number":8,"palace_name":"艮","direction":"東北","base_star":3,"sitting_star":6,"facing_star":1,"facing_star_name":"一白貪狼星 (水)"},
            {"palace_number":9,"palace_name":"離","direction":"南","base_star":4,"sitting_star":5,"facing_star":9,"facing_star_name":"九紫右弼星 (火)"}
        ],
        "engine_name": "Xuan Kong Flying Stars Engine",
        "system_type": "xiang_xue",
        "calculation_timestamp": "fixed"
    });
    assert_eq!(actual, expected);
}

#[test]
fn xuankong_preserves_f64_precision_at_mountain_boundaries() {
    let before = calculate_xuankong_chart_rust(337.499_999, 9, "fixed");
    let boundary = calculate_xuankong_chart_rust(337.5, 9, "fixed");
    assert_eq!(before["facing_mountain"], "亥 (乾卦 - 陽)");
    assert_eq!(boundary["facing_mountain"], "壬 (坎卦 - 陽)");
    assert!((before["facing_degree"].as_f64().unwrap() - 337.499_999).abs() <= 1e-6);
}

fn assert_json_close(actual: &Value, expected: &Value, path: &str) {
    match (actual, expected) {
        (Value::Number(actual), Value::Number(expected))
            if actual.is_f64() || expected.is_f64() =>
        {
            let difference = (actual.as_f64().unwrap() - expected.as_f64().unwrap()).abs();
            assert!(
                difference <= 1e-6,
                "float mismatch at {path}: {actual} != {expected}"
            );
        }
        (Value::Array(actual), Value::Array(expected)) => {
            assert_eq!(
                actual.len(),
                expected.len(),
                "array length mismatch at {path}"
            );
            for (index, (actual, expected)) in actual.iter().zip(expected).enumerate() {
                assert_json_close(actual, expected, &format!("{path}[{index}]"));
            }
        }
        (Value::Object(actual), Value::Object(expected)) => {
            let actual_keys: std::collections::BTreeSet<_> = actual.keys().collect();
            let expected_keys: std::collections::BTreeSet<_> = expected.keys().collect();
            assert_eq!(actual_keys, expected_keys, "object keys mismatch at {path}");
            for (key, expected) in expected {
                assert_json_close(&actual[key], expected, &format!("{path}.{key}"));
            }
        }
        _ => assert_eq!(actual, expected, "value mismatch at {path}"),
    }
}

#[test]
#[ignore = "explicit deterministic 10,000-case cross-language parity gate"]
fn randomized_10000_case_engine_parity() {
    let project_root = std::path::Path::new(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .unwrap();
    let mut child = Command::new("python3")
        .arg("rust_core/tests/python_engine_oracle.py")
        .arg("--count")
        .arg("10000")
        .current_dir(project_root)
        .env("HORO_ALLOW_PYTHON_FALLBACK", "1")
        .stdout(Stdio::piped())
        .spawn()
        .expect("start Python engine oracle");
    let stdout = child.stdout.take().expect("capture Python oracle stdout");
    let mut compared = 0_usize;
    for line in BufReader::new(stdout).lines() {
        let record: Value =
            serde_json::from_str(&line.expect("read oracle line")).expect("parse oracle JSON");
        let input = &record["input"];
        let mut actual = match record["engine"].as_str().unwrap() {
            "ziwei" => calculate_ziwei_chart_rust(
                input["year"].as_i64().unwrap() as i32,
                input["month"].as_i64().unwrap() as i32,
                input["day"].as_i64().unwrap() as i32,
                input["hour"].as_i64().unwrap() as i32,
                input["gender"].as_str().unwrap(),
                "fixed",
            ),
            "qimen" => calculate_qimen_chart_rust(
                input["year"].as_i64().unwrap() as i32,
                input["month"].as_i64().unwrap() as i32,
                input["day"].as_i64().unwrap() as i32,
                input["hour"].as_i64().unwrap() as i32,
                None,
                "fixed",
            ),
            "xuankong" => calculate_xuankong_chart_rust(
                input["facing_degree"].as_f64().unwrap(),
                input["period"].as_i64().unwrap() as i32,
                "fixed",
            ),
            "thai_vedic" => calculate_thai_vedic_chart_rust(
                input["year"].as_i64().unwrap() as i32,
                input["month"].as_i64().unwrap() as i32,
                input["day"].as_i64().unwrap() as i32,
                input["hour"].as_i64().unwrap() as i32,
                input["day_of_week"].as_i64().unwrap() as i32,
                "fixed",
            ),
            "iching" => {
                let lines: Vec<i32> = input["lines"]
                    .as_array()
                    .unwrap()
                    .iter()
                    .map(|line| line.as_i64().unwrap() as i32)
                    .collect();
                calculate_iching_chart_rust(input["day_stem"].as_str().unwrap(), &lines, "fixed")
                    .unwrap()
            }
            "liuren" => calculate_liuren_chart_rust(
                input["day_stem"].as_str().unwrap(),
                input["day_branch"].as_str().unwrap(),
                input["month_general"].as_str().unwrap(),
                input["hour_branch"].as_str().unwrap(),
                "fixed",
            )
            .unwrap(),
            "zeji" => calculate_zeji_chart_rust(
                input["year_branch"].as_str().unwrap(),
                input["month_branch"].as_str().unwrap(),
                input["day_branch"].as_str().unwrap(),
                input["user_birth_branch"].as_str(),
                "fixed",
            )
            .unwrap(),
            "satta_lek" => calculate_satta_lek_chart_rust(
                input["day_num"].as_i64().unwrap(),
                input["lunar_month"].as_i64().unwrap(),
                input["year_zodiac_num"].as_i64().unwrap(),
                "fixed",
            )
            .unwrap(),
            "numerology_score" => {
                calculate_numerology_score_rust(input["text"].as_str().unwrap(), "fixed")
            }
            engine => panic!("unexpected oracle engine {engine}"),
        };
        actual
            .as_object_mut()
            .unwrap()
            .remove("calculation_timestamp");
        assert_json_close(&actual, &record["chart"], &format!("$[{compared}]"));
        compared += 1;
    }
    assert!(child.wait().expect("wait for Python oracle").success());
    assert_eq!(compared, 10_000);
}

#[test]
fn ziwei_extreme_year_input_does_not_overflow() {
    let chart = calculate_ziwei_chart_rust(i32::MIN, 1, 1, i32::MAX, "male", "fixed");
    assert_eq!(chart["engine"], "ZiWeiEngine");
}

#[test]
fn thai_vedic_extreme_numeric_input_does_not_overflow() {
    let chart =
        calculate_thai_vedic_chart_rust(i32::MIN, i32::MIN, i32::MAX, i32::MIN, i32::MAX, "fixed");
    assert_eq!(chart["engine"], "ThaiVedicEngine");
}

#[test]
fn satta_lek_extreme_numeric_input_does_not_overflow() {
    let chart = calculate_satta_lek_chart_rust(i64::MAX, i64::MIN, i64::MAX, "fixed").unwrap();
    assert_eq!(chart["matrix_7_base"].as_array().unwrap().len(), 7);
}

#[test]
#[ignore = "explicit deterministic 100,000-input panic-safety gate"]
fn invalid_100000_inputs_do_not_panic() {
    let mut state = 0x7f4a_7c15_d3e9_b129_u64;
    for index in 0..100_000_u64 {
        state = state
            .wrapping_mul(6_364_136_223_846_793_005)
            .wrapping_add(1);
        let value = (state >> 32) as i32;
        let _ = calculate_ziwei_chart_rust(value, value, value, value, "invalid", "fixed");
        let _ = calculate_qimen_chart_rust(value, value, value, value, None, "fixed");
        let degree = match index % 97 {
            0 => f64::NAN,
            1 => f64::INFINITY,
            _ => f64::from(value) / 1_000_000.0,
        };
        let _ = calculate_xuankong_chart_rust(degree, value, "fixed");
        let _ = calculate_thai_vedic_chart_rust(value, value, value, value, value, "fixed");
        let invalid_lines = [value, 0, 1, 2, 3, 4, 5];
        let _ = calculate_iching_chart_rust("invalid", &invalid_lines, "fixed");
        let _ = calculate_liuren_chart_rust("invalid", "invalid", "invalid", "invalid", "fixed");
        let _ =
            calculate_zeji_chart_rust("invalid", "invalid", "invalid", Some("invalid"), "fixed");
        let _ = calculate_satta_lek_chart_rust(i64::from(value), i64::MIN, i64::MAX, "fixed");
        let _ = calculate_numerology_score_rust("invalid-ทดสอบ-123", "fixed");
    }
}

fn complete_rust_endpoint(engine: &str, payload_text: &str) -> Vec<u8> {
    let input: Value = serde_json::from_str(payload_text).unwrap();
    let timestamp = chrono::Utc::now().to_rfc3339();
    let chart = match engine {
        "ziwei" => calculate_ziwei_chart_rust(
            input["year"].as_i64().unwrap() as i32,
            input["month"].as_i64().unwrap() as i32,
            input["day"].as_i64().unwrap() as i32,
            input["hour"].as_i64().unwrap() as i32,
            input["gender"].as_str().unwrap(),
            &timestamp,
        ),
        "qimen" => calculate_qimen_chart_rust(
            input["year"].as_i64().unwrap() as i32,
            input["month"].as_i64().unwrap() as i32,
            input["day"].as_i64().unwrap() as i32,
            input["hour"].as_i64().unwrap() as i32,
            None,
            &timestamp,
        ),
        "xuankong" => calculate_xuankong_chart_rust(
            input["facing_degree"].as_f64().unwrap(),
            input["period"].as_i64().unwrap() as i32,
            &timestamp,
        ),
        "thai_vedic" => calculate_thai_vedic_chart_rust(
            input["year"].as_i64().unwrap() as i32,
            input["month"].as_i64().unwrap() as i32,
            input["day"].as_i64().unwrap() as i32,
            input["hour"].as_i64().unwrap() as i32,
            input["day_of_week"].as_i64().unwrap() as i32,
            &timestamp,
        ),
        "iching" => {
            let lines: Vec<i32> = input["lines"]
                .as_array()
                .unwrap()
                .iter()
                .map(|line| line.as_i64().unwrap() as i32)
                .collect();
            calculate_iching_chart_rust(input["day_stem"].as_str().unwrap(), &lines, &timestamp)
                .unwrap()
        }
        "liuren" => calculate_liuren_chart_rust(
            input["day_stem"].as_str().unwrap(),
            input["day_branch"].as_str().unwrap(),
            input["month_general"].as_str().unwrap(),
            input["hour_branch"].as_str().unwrap(),
            &timestamp,
        )
        .unwrap(),
        "zeji" => calculate_zeji_chart_rust(
            input["year_branch"].as_str().unwrap(),
            input["month_branch"].as_str().unwrap(),
            input["day_branch"].as_str().unwrap(),
            input["user_birth_branch"].as_str(),
            &timestamp,
        )
        .unwrap(),
        "numerology" => calculate_satta_lek_chart_rust(
            input["day_num"].as_i64().unwrap(),
            input["lunar_month"].as_i64().unwrap(),
            input["year_zodiac_num"].as_i64().unwrap(),
            &timestamp,
        )
        .unwrap(),
        _ => unreachable!(),
    };
    serde_json::to_vec(&chart).unwrap()
}

fn percentile_95(samples: &mut [u128]) -> u128 {
    samples.sort_unstable();
    samples[(samples.len() - 1) * 95 / 100]
}

#[test]
#[ignore = "explicit complete-request ROI benchmark"]
fn benchmark_complete_engine_requests_reports_roi_gates() {
    const COUNT: usize = 2_000;
    let project_root = std::path::Path::new(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .unwrap();
    let output = Command::new("python3")
        .arg("rust_core/tests/python_engine_oracle.py")
        .arg("--benchmark")
        .arg("--count")
        .arg(COUNT.to_string())
        .current_dir(project_root)
        .env("HORO_ALLOW_PYTHON_FALLBACK", "1")
        .output()
        .expect("run Python endpoint benchmark");
    assert!(
        output.status.success(),
        "Python benchmark failed: {}",
        String::from_utf8_lossy(&output.stderr)
    );
    let python: Value =
        serde_json::from_slice(&output.stdout).expect("parse Python benchmark JSON");
    let branches = [
        "子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥",
    ];
    let stems = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"];
    let month_generals = [
        "正月",
        "二月",
        "三月",
        "四月",
        "五月",
        "六月",
        "七月",
        "八月",
        "九月",
        "十月",
        "十一月",
        "十二月",
    ];
    for engine in [
        "ziwei",
        "qimen",
        "xuankong",
        "thai_vedic",
        "iching",
        "liuren",
        "zeji",
        "numerology",
    ] {
        let requests: Vec<String> = (0..COUNT).map(|index| match engine {
            "ziwei" => json!({"year":1900+index%201,"month":1+index%12,"day":1+index%28,"hour":index%24,"gender":"male"}).to_string(),
            "qimen" => json!({"year":1900+index%201,"month":1+index%12,"day":1+index%28,"hour":index%24}).to_string(),
            "xuankong" => json!({"facing_degree":(index*1_000_003%360_000_000) as f64/1_000_000.0,"period":9}).to_string(),
            "thai_vedic" => json!({"year":1900+index%201,"month":1+index%12,"day":1+index%28,"hour":index%24,"day_of_week":index%8}).to_string(),
            "iching" => json!({"day_stem":stems[index%10],"lines":(0..6).map(|offset|6+(index+offset)%4).collect::<Vec<_>>()}).to_string(),
            "liuren" => json!({"day_stem":stems[index%10],"day_branch":branches[index%12],"month_general":month_generals[index%12],"hour_branch":branches[(index*5)%12]}).to_string(),
            "zeji" => json!({"year_branch":branches[index%12],"month_branch":branches[(index*3)%12],"day_branch":branches[(index*7)%12],"user_birth_branch":branches[(index*11)%12]}).to_string(),
            "numerology" => json!({"day_num":1+index%31,"lunar_month":1+index%12,"year_zodiac_num":1+index%12}).to_string(),
            _ => unreachable!(),
        }).collect();
        for request in requests.iter().take(20) {
            let _ = complete_rust_endpoint(engine, request);
        }
        let cpu_start = process_cpu_time_ns();
        let mut wall_samples = Vec::with_capacity(COUNT);
        for request in &requests {
            let started = Instant::now();
            let _ = complete_rust_endpoint(engine, request);
            wall_samples.push(started.elapsed().as_nanos());
        }
        let rust_cpu = (process_cpu_time_ns() - cpu_start) as f64 / COUNT as f64;
        let rust_p95 = percentile_95(&mut wall_samples) as f64;
        let python_p95 = python[engine]["p95_ns"].as_f64().unwrap();
        let python_cpu = python[engine]["cpu_per_request_ns"].as_f64().unwrap();
        let p95_improvement = 1.0 - rust_p95 / python_p95;
        let cpu_reduction = 1.0 - rust_cpu / python_cpu;
        let decision = if p95_improvement >= 0.20 && cpu_reduction >= 0.30 {
            "QUALIFIED"
        } else {
            "PARKED"
        };
        println!(
            "[INFO] {}_ROI decision={} rust_p95_ns={:.0} python_p95_ns={:.0} p95_improvement={:.2}% rust_cpu_per_request_ns={:.0} python_cpu_per_request_ns={:.0} cpu_reduction={:.2}%",
            engine.to_uppercase(), decision, rust_p95, python_p95, p95_improvement * 100.0,
            rust_cpu, python_cpu, cpu_reduction * 100.0,
        );
    }
    let mut metrics = MetricsRegistry::default();
    for index in 0..20 {
        metrics.record_request("GET", &format!("/api/{}", index % 4), 200, 0.001);
        let _ = metrics.generate_metrics_text(12.34);
    }
    let cpu_start = process_cpu_time_ns();
    let mut wall_samples = Vec::with_capacity(COUNT);
    for index in 0..COUNT {
        let started = Instant::now();
        metrics.record_request("GET", &format!("/api/{}", index % 4), 200, 0.001);
        let _ = metrics.generate_metrics_text(12.34);
        wall_samples.push(started.elapsed().as_nanos());
    }
    let rust_cpu = (process_cpu_time_ns() - cpu_start) as f64 / COUNT as f64;
    let rust_p95 = percentile_95(&mut wall_samples) as f64;
    let python_p95 = python["metrics"]["p95_ns"].as_f64().unwrap();
    let python_cpu = python["metrics"]["cpu_per_request_ns"].as_f64().unwrap();
    let p95_improvement = 1.0 - rust_p95 / python_p95;
    let cpu_reduction = 1.0 - rust_cpu / python_cpu;
    let decision = if p95_improvement >= 0.20 && cpu_reduction >= 0.30 {
        "QUALIFIED"
    } else {
        "PARKED"
    };
    println!(
        "[INFO] METRICS_ROI decision={} rust_p95_ns={:.0} python_p95_ns={:.0} p95_improvement={:.2}% rust_cpu_per_request_ns={:.0} python_cpu_per_request_ns={:.0} cpu_reduction={:.2}%",
        decision, rust_p95, python_p95, p95_improvement * 100.0,
        rust_cpu, python_cpu, cpu_reduction * 100.0,
    );
}

#[cfg(any(target_os = "linux", target_os = "macos"))]
fn process_cpu_time_ns() -> u128 {
    #[repr(C)]
    struct Timespec {
        seconds: i64,
        nanoseconds: i64,
    }
    unsafe extern "C" {
        fn clock_gettime(clock_id: i32, time: *mut Timespec) -> i32;
    }
    #[cfg(target_os = "linux")]
    const CLOCK_PROCESS_CPUTIME_ID: i32 = 2;
    #[cfg(target_os = "macos")]
    const CLOCK_PROCESS_CPUTIME_ID: i32 = 12;
    let mut time = Timespec {
        seconds: 0,
        nanoseconds: 0,
    };
    let status = unsafe { clock_gettime(CLOCK_PROCESS_CPUTIME_ID, &mut time) };
    assert_eq!(status, 0, "clock_gettime failed");
    time.seconds as u128 * 1_000_000_000 + time.nanoseconds as u128
}

#[cfg(not(any(target_os = "linux", target_os = "macos")))]
fn process_cpu_time_ns() -> u128 {
    Instant::now().elapsed().as_nanos()
}
