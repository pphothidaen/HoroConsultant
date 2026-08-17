/*!
 * rust_core/src/bin/vercel_curl_regression.rs
 * High-Performance Async Rust Vercel Edge Gateway Curl Regression Tester.
 */

use reqwest::header::{HeaderMap, HeaderValue};
use reqwest::Client;
use serde::{Deserialize, Serialize};
use std::env;
use std::error::Error;
use std::time::Instant;

const ORIGIN: &str = "https://pphothidaen-horoconsultant-core-backend.static.hf.space";
const DEFAULT_BASE_URL: &str = "https://horo-consultant-psi.vercel.app";

#[derive(Serialize, Deserialize, Debug)]
struct CheckResult {
    id: String,
    name: String,
    url: String,
    method: String,
    status_code: u16,
    passed: bool,
    latency_ms: f64,
    cors_ok: bool,
    details: String,
}

#[derive(Serialize, Deserialize, Debug)]
struct FinalReport {
    timestamp: String,
    target_url: String,
    total_checks: usize,
    passed_count: usize,
    failed_count: usize,
    overall_status: String,
    checks: Vec<CheckResult>,
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn Error>> {
    println!("[INFO] Starting High-Performance Async Rust Vercel Curl Regression Suite...");

    let args: Vec<String> = env::args().collect();
    let mut base_url = DEFAULT_BASE_URL.to_string();

    let mut i = 1;
    while i < args.len() {
        if args[i] == "--url" && i + 1 < args.len() {
            base_url = args[i + 1].clone();
            i += 1;
        }
        i += 1;
    }

    println!("[INFO] Target Gateway Base URL: {}", base_url);

    let client = Client::builder()
        .timeout(std::time::Duration::from_secs(30))
        .build()?;

    let mut headers = HeaderMap::new();
    headers.insert("accept", HeaderValue::from_static("*/*"));
    headers.insert("origin", HeaderValue::from_static(ORIGIN));
    headers.insert(
        "user-agent",
        HeaderValue::from_static(
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Rust/VercelCurlSuite",
        ),
    );

    let mut checks = Vec::new();

    // Check 1: GET /health
    let health_url = format!("{}/health", base_url.trim_end_matches('/'));
    let start = Instant::now();
    let resp = client
        .get(&health_url)
        .headers(headers.clone())
        .send()
        .await;
    let elapsed = start.elapsed().as_secs_f64() * 1000.0;

    match resp {
        Ok(r) => {
            let status = r.status().as_u16();
            let cors_ok = r.headers().contains_key("access-control-allow-origin");
            let body = r.text().await.unwrap_or_default();
            let json_ok = body.contains("ok") || body.contains("status");
            let passed = (status == 200) && json_ok;
            checks.push(CheckResult {
                id: "CHK-01".to_string(),
                name: "GET /health Endpoint & CORS".to_string(),
                url: health_url,
                method: "GET".to_string(),
                status_code: status,
                passed,
                latency_ms: elapsed,
                cors_ok,
                details: format!("JSON OK: {}, Body length: {}", json_ok, body.len()),
            });
        }
        Err(e) => {
            checks.push(CheckResult {
                id: "CHK-01".to_string(),
                name: "GET /health Endpoint & CORS".to_string(),
                url: health_url,
                method: "GET".to_string(),
                status_code: 0,
                passed: false,
                latency_ms: elapsed,
                cors_ok: false,
                details: format!("Network Error: {}", e),
            });
        }
    }

    // Check 2: OPTIONS /api/v1/bazi/interpret
    let opts_url = format!("{}/api/v1/bazi/interpret", base_url.trim_end_matches('/'));
    let start = Instant::now();
    let resp = client
        .request(reqwest::Method::OPTIONS, &opts_url)
        .headers(headers.clone())
        .send()
        .await;
    let elapsed = start.elapsed().as_secs_f64() * 1000.0;

    match resp {
        Ok(r) => {
            let status = r.status().as_u16();
            let cors_ok = r.headers().contains_key("access-control-allow-origin")
                || r.headers().contains_key("access-control-allow-methods");
            let passed = (status == 200 || status == 204) && cors_ok;
            checks.push(CheckResult {
                id: "CHK-02".to_string(),
                name: "OPTIONS /api/v1/bazi/interpret Preflight".to_string(),
                url: opts_url,
                method: "OPTIONS".to_string(),
                status_code: status,
                passed,
                latency_ms: elapsed,
                cors_ok,
                details: format!("Status: {}", status),
            });
        }
        Err(e) => {
            checks.push(CheckResult {
                id: "CHK-02".to_string(),
                name: "OPTIONS /api/v1/bazi/interpret Preflight".to_string(),
                url: opts_url,
                method: "OPTIONS".to_string(),
                status_code: 0,
                passed: false,
                latency_ms: elapsed,
                cors_ok: false,
                details: format!("Network Error: {}", e),
            });
        }
    }

    // Check 3: POST /api/v1/bazi/interpret
    let post_url = format!("{}/api/v1/bazi/interpret", base_url.trim_end_matches('/'));
    let payload = serde_json::json!({
        "year": 1990,
        "month": 5,
        "day": 15,
        "hour": 14,
        "minute": 30,
        "gender": "male",
        "name": "Test User"
    });

    let mut post_headers = headers.clone();
    post_headers.insert("content-type", HeaderValue::from_static("application/json"));

    let start = Instant::now();
    let resp = client
        .post(&post_url)
        .headers(post_headers)
        .json(&payload)
        .send()
        .await;
    let elapsed = start.elapsed().as_secs_f64() * 1000.0;

    match resp {
        Ok(r) => {
            let status = r.status().as_u16();
            let cors_ok = r.headers().contains_key("access-control-allow-origin");
            let body = r.text().await.unwrap_or_default();
            let has_chart =
                body.contains("chart") || body.contains("bazi") || body.contains("day_master");
            let passed = (status == 200) && has_chart;
            checks.push(CheckResult {
                id: "CHK-03".to_string(),
                name: "POST /api/v1/bazi/interpret Execution".to_string(),
                url: post_url,
                method: "POST".to_string(),
                status_code: status,
                passed,
                latency_ms: elapsed,
                cors_ok,
                details: format!(
                    "Chart Present: {}, Response Length: {}",
                    has_chart,
                    body.len()
                ),
            });
        }
        Err(e) => {
            checks.push(CheckResult {
                id: "CHK-03".to_string(),
                name: "POST /api/v1/bazi/interpret Execution".to_string(),
                url: post_url,
                method: "POST".to_string(),
                status_code: 0,
                passed: false,
                latency_ms: elapsed,
                cors_ok: false,
                details: format!("Network Error: {}", e),
            });
        }
    }

    let passed_count = checks.iter().filter(|c| c.passed).count();
    let total_checks = checks.len();
    let failed_count = total_checks - passed_count;
    let overall_status = if failed_count == 0 {
        "PASSED 100%".to_string()
    } else {
        "FAILED".to_string()
    };

    let report = FinalReport {
        timestamp: chrono::Utc::now().to_rfc3339(),
        target_url: base_url,
        total_checks,
        passed_count,
        failed_count,
        overall_status: overall_status.clone(),
        checks,
    };

    println!("\n============================================================");
    println!("🏆 VERCEL CURL REGRESSION REPORT: {}", overall_status);
    println!("============================================================");
    for c in &report.checks {
        let icon = if c.passed { "✅" } else { "❌" };
        println!(
            "{} [{}] {} {} -> HTTP {} ({:.1} ms)",
            icon, c.id, c.method, c.name, c.status_code, c.latency_ms
        );
    }

    let report_json = serde_json::to_string_pretty(&report)?;
    std::fs::write(
        "project/tests/vercel_curl_regression_report.json",
        report_json,
    )?;
    println!("\n[INFO] Saved report to project/tests/vercel_curl_regression_report.json");

    if failed_count > 0 {
        Err("One or more regression checks failed".into())
    } else {
        Ok(())
    }
}
