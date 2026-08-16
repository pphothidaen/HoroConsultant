/*!
 * rust_core/src/zeji.rs
 * High-performance Imperial Calendar Date Selection (擇吉學) Duty Officers matrix core.
 */

#[cfg(feature = "python")]
use pyo3::prelude::*;
use serde_json::{json, Value};

static BRANCHES: [&str; 12] = [
    "子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥",
];

static DUTY_OFFICERS: [&str; 12] = [
    "建日", "除日", "滿日", "平日", "定日", "執日", "破日", "危日", "成日", "收日", "開日", "閉日",
];

static OFFICER_DESCRIPTIONS: [&str; 12] = [
    "健旺之日。宜開創、上任、祈福；忌動土、開倉。",
    "掃除惡氣。宜沐浴、求醫、解除、清潔；忌求官、開張。",
    "圓滿豐收。宜開市、立券、祭祀；忌動土、服藥。",
    "平正和洽。宜修路、塗泥、平基；忌爭執、祈福。",
    "安定不動。宜冠帶、立券、訂婚、安床；忌出行、詞訟。",
    "執持固守。宜捕捉、結婚、建造；忌搬家、遠行。",
    "衝破不和。宜破屋、壞垣、求醫；忌辦喜事、開張。",
    "高危警惕。宜祭祀、祈福；忌登高、乘船、冒險。",
    "成就成功。宜結婚、開市、入學、赴任；忌爭端、詞訟。",
    "收藏收穫。宜收帳、進人口、置產；忌安葬、出行。",
    "開放光明。宜開市、結婚、出行、建造；忌安葬、破土。",
    "堅閉收斂。宜築堤、補垣、埋穴；忌開光、求醫。",
];

fn branch_index(branch: &str) -> Result<usize, String> {
    BRANCHES
        .iter()
        .position(|&candidate| candidate == branch)
        .ok_or_else(|| format!("invalid Earth Branch: {branch}"))
}

/// Build the complete Ze Ji suitability response with validation at the wire
/// boundary instead of silently treating unknown branches as Zi.
pub fn calculate_zeji_chart_rust(
    year_branch: &str,
    month_branch: &str,
    day_branch: &str,
    user_birth_branch: Option<&str>,
    calculation_timestamp: &str,
) -> Result<Value, String> {
    let year_index = branch_index(year_branch)?;
    let month_index = branch_index(month_branch)?;
    let day_index = branch_index(day_branch)?;
    let user_index = user_birth_branch.map(branch_index).transpose()?;
    let officer_index = (day_index + 12 - month_index) % 12;
    let officer = DUTY_OFFICERS[officer_index];
    let is_year_breaker = (year_index + 6) % 12 == day_index;
    let is_month_breaker = (month_index + 6) % 12 == day_index;
    let is_user_clash = user_index.map(|index| (index + 6) % 12 == day_index);
    let (rating, status) = if is_year_breaker || is_month_breaker || officer == "破日" {
        (1, "凶 - 大事不宜 (歲破/月破/破日)")
    } else if is_user_clash == Some(true) {
        (2, "平凶 - 衝剋個人生肖")
    } else if matches!(officer, "成日" | "開日" | "滿日") {
        (5, "吉 - 百事大吉")
    } else if matches!(officer, "建日" | "除日" | "定日") {
        (4, "吉 - 宜開創求醫")
    } else {
        (3, "平 - 諸事平順")
    };
    let marriage = matches!(officer, "成日" | "開日" | "定日" | "執日") && !is_year_breaker;
    let opening = matches!(officer, "成日" | "開日" | "滿日" | "建日") && !is_year_breaker;
    let moving = matches!(officer, "成日" | "開日" | "定日") && !is_year_breaker;
    let travel = matches!(officer, "開日" | "成日");
    let medical = matches!(officer, "除日" | "破日");

    Ok(json!({
        "engine": "ZeJiEngine",
        "duty_officer": officer,
        "duty_description": OFFICER_DESCRIPTIONS[officer_index],
        "rating_stars": rating,
        "overall_status": status,
        "is_year_breaker": is_year_breaker,
        "is_month_breaker": is_month_breaker,
        "is_user_clash": is_user_clash,
        "activities_suitability": {
            "結婚訂婚": if marriage { "宜" } else { "忌" },
            "開市開業": if opening { "宜" } else { "忌" },
            "搬家入宅": if moving { "宜" } else { "忌" },
            "出行遠遊": if travel { "宜" } else { "忌" },
            "求醫治病": if medical { "宜" } else { "平" },
        },
        "engine_name": "Imperial Calendar Date Selection Engine",
        "system_type": "ze_ji",
        "calculation_timestamp": calculation_timestamp,
    }))
}

pub fn calculate_zeji_duty_officer_rust(month_branch: &str, day_branch: &str) -> String {
    let month_idx = BRANCHES
        .iter()
        .position(|&b| b == month_branch)
        .unwrap_or(0);
    let day_idx = BRANCHES.iter().position(|&b| b == day_branch).unwrap_or(0);
    let officer_idx = (day_idx + 12 - month_idx) % 12;
    DUTY_OFFICERS[officer_idx].to_string()
}

pub fn check_branch_clash_rust(day_branch: &str, target_branch: &str) -> bool {
    let day_idx = BRANCHES.iter().position(|&b| b == day_branch).unwrap_or(0);
    let target_idx = BRANCHES
        .iter()
        .position(|&b| b == target_branch)
        .unwrap_or(0);
    (day_idx + 6) % 12 == target_idx
}

/// Calculate 12 Duty Officer name for Date Selection based on Month Branch and Day Branch.
#[cfg(feature = "python")]
#[pyfunction]
pub fn calculate_zeji_duty_officer(
    py: Python<'_>,
    month_branch: &str,
    day_branch: &str,
) -> PyResult<String> {
    let month_branch = month_branch.to_owned();
    let day_branch = day_branch.to_owned();
    let result = py.allow_threads(move || {
        let month_idx = BRANCHES
            .iter()
            .position(|&b| b == month_branch)
            .unwrap_or(0);
        let day_idx = BRANCHES.iter().position(|&b| b == day_branch).unwrap_or(0);
        let officer_idx = (day_idx + 12 - month_idx) % 12;
        DUTY_OFFICERS[officer_idx].to_string()
    });
    Ok(result)
}

/// Check if Day Branch conflicts (clashes) with Month Branch (Month Breaker 月破) or Year Branch (Year Breaker 歲破).
#[cfg(feature = "python")]
#[pyfunction]
pub fn check_branch_clash(py: Python<'_>, day_branch: &str, target_branch: &str) -> PyResult<bool> {
    let day_branch = day_branch.to_owned();
    let target_branch = target_branch.to_owned();
    let result = py.allow_threads(move || {
        let day_idx = BRANCHES.iter().position(|&b| b == day_branch).unwrap_or(0);
        let target_idx = BRANCHES
            .iter()
            .position(|&b| b == target_branch)
            .unwrap_or(0);
        // Opposite branches clash (distance of 6)
        (day_idx + 6) % 12 == target_idx
    });
    Ok(result)
}
