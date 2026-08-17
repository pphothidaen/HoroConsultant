/*!
 * rust_core/src/bin/button_regression.rs
 * High-Performance Async Rust UI Button & Endpoint Contract Regression Tester.
 */

use reqwest::Client;
use serde::{Deserialize, Serialize};
use std::error::Error;
use std::fs;
use std::path::Path;
use std::time::Instant;
use tokio;

#[derive(Serialize, Deserialize, Debug)]
struct TestResult {
    id: String,
    label: String,
    status: String,
    http_code: u16,
    latency_ms: f64,
}

#[derive(Serialize, Deserialize, Debug)]
struct FinalReport {
    timestamp: String,
    total_tested: usize,
    passed_count: usize,
    failed_count: usize,
    overall_status: String,
    results: Vec<TestResult>,
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn Error>> {
    println!("[INFO] Starting High-Performance Async Rust UI Button Regression Test Suite...");

    let base_url =
        std::env::var("TEST_BASE_URL").unwrap_or_else(|_| "http://testserver".to_string());
    let client = Client::builder()
        .timeout(std::time::Duration::from_secs(10))
        .build()?;

    let contracts = vec![
        ("BTN-IDX-02", "ค้นหา & เติมค่า (Location Search)", "POST", "/api/v1/location/resolve", 200),
        ("BTN-IDX-03", "Preset: กรุงเทพฯ", "GET", "/", 200),
        ("BTN-IDX-04", "Preset: สิงคโปร์", "GET", "/", 200),
        ("BTN-IDX-05", "Preset: นิวยอร์ก", "GET", "/", 200),
        ("BTN-IDX-06", "紫微 紫微斗數 (Zi Wei)", "GET", "/api/v1/ziwei/calculate?year=1990&month=5&day=15&hour=14&gender=male", 200),
        ("BTN-IDX-07", "奇門 奇門遁甲 (Qi Men)", "GET", "/api/v1/qimen/calculate?year=2026&month=8&day=7&hour=14", 200),
        ("BTN-IDX-08", "六壬 大六壬 (Da Liu Ren)", "GET", "/api/v1/liuren/calculate?day_stem=%E7%94%B2&day_branch=%E5%AD%90&month_general=%E6%AD%A3%E6%9C%88&hour_branch=%E5%8D%88", 200),
        ("BTN-IDX-09", "易經 易經六爻 (I Ching)", "GET", "/api/v1/iching/calculate?day_stem=%E7%94%B2", 200),
        ("BTN-IDX-10", "風水 玄空風水 (Xuan Kong)", "GET", "/api/v1/xuankong/calculate?facing_degree=180.0&period=9", 200),
        ("BTN-IDX-11", "擇吉 擇吉คำนวณฤกษ์ (Ze Ji)", "GET", "/api/v1/zeji/calculate?year_branch=%E5%8D%88&month_branch=%E7%94%B3&day_branch=%E5%AF%85&user_birth_branch=%E5%AD%90", 200),
        ("BTN-IDX-12", "🐘 โหราศาสตร์ไทย & ภารตวิทยา", "GET", "/api/v1/thaivedic/calculate?year=1990&month=5&day=15&hour=14&day_of_week=2", 200),
        ("BTN-IDX-13", "🌌 โหราศาสตร์สากล & ยูเรเนียน", "GET", "/api/v1/western/calculate?year=1990&month=5&day=15&hour=14", 200),
        ("BTN-IDX-14", "🔢 สัตตเลข 7 ฐาน & เลขศาสตร์", "GET", "/api/v1/numerology/calculate?text=0812345678&day_num=2&lunar_month=6&year_zodiac_num=7", 200),
        ("BTN-IDX-15", "Tab: บทตีความ / Gemini Audit / RAG", "GET", "/", 200),
        ("BTN-ADM-01", "Authorized Email Login Button", "POST", "/admin/auth/google", 200),
        ("BTN-ADM-02", "Logout Admin Button", "GET", "/admin", 200),
        ("BTN-HTL-01", "⚡ Batch Draft Button", "POST", "/hitl/batch-draft", 200),
        ("BTN-HTL-02", "⬇ Export JSONL Button", "GET", "/hitl/export", 200),
        ("BTN-HTL-03", "⚡ Single Generate Draft Button", "POST", "/hitl/draft/CM-BZ-001", 404),
        ("BTN-HTL-04", "✅ Approve Button", "POST", "/hitl/review/CM-BZ-001", 404),
        ("BTN-HTL-05", "↩ Undo Decision Button", "DELETE", "/hitl/review/CM-BZ-001", 404),
        ("BTN-DOC-01", "📘 Swagger Interactive API Docs", "GET", "/docs", 200),
        ("BTN-DOC-02", "📕 ReDoc Schema Explorer", "GET", "/redoc", 200),
        ("BTN-DOC-03", "⚙️ OpenAPI JSON Specification", "GET", "/openapi.json", 200),
    ];

    let mut results = Vec::new();
    let mut passed = 0;
    let mut failed = 0;

    for (id, label, method, path, expected_status) in contracts {
        let start = Instant::now();
        let full_url = format!("{}{}", base_url, path);

        let req_builder = match method {
            "POST" => client.post(&full_url),
            "DELETE" => client.delete(&full_url),
            _ => client.get(&full_url),
        };

        let status_res = req_builder.send().await;
        let elapsed = start.elapsed().as_secs_f64() * 1000.0;

        match status_res {
            Ok(resp) => {
                let code = resp.status().as_u16();
                let is_pass = code == expected_status;
                if is_pass {
                    passed += 1;
                    println!("[OK] {} - {}: PASSED ({:.2}ms)", id, label, elapsed);
                } else {
                    failed += 1;
                    println!(
                        "[FAIL] {} - {}: Expected {} got {}",
                        id, label, expected_status, code
                    );
                }
                results.push(TestResult {
                    id: id.to_string(),
                    label: label.to_string(),
                    status: if is_pass {
                        "PASSED".to_string()
                    } else {
                        "FAILED".to_string()
                    },
                    http_code: code,
                    latency_ms: elapsed,
                });
            }
            Err(e) => {
                failed += 1;
                println!("[ERROR] {} - {}: Connection error: {}", id, label, e);
                results.push(TestResult {
                    id: id.to_string(),
                    label: label.to_string(),
                    status: "ERROR".to_string(),
                    http_code: 0,
                    latency_ms: elapsed,
                });
            }
        }
    }

    let report = FinalReport {
        timestamp: chrono::Utc::now().to_rfc3339(),
        total_tested: results.len(),
        passed_count: passed,
        failed_count: failed,
        overall_status: if failed == 0 {
            "PASSED".to_string()
        } else {
            "FAILED".to_string()
        },
        results,
    };

    let report_json = serde_json::to_string_pretty(&report)?;
    let out_path = Path::new("project/tests/rust_button_regression_report.json");
    if let Some(parent) = out_path.parent() {
        fs::create_dir_all(parent)?;
    }
    fs::write(out_path, report_json)?;

    println!(
        "[INFO] Rust Button Regression Report written to {:?}",
        out_path
    );
    println!(
        "[SUMMARY] Passed: {} / Total: {}",
        passed, report.total_tested
    );

    Ok(())
}
