/*!
 * rust_core/src/bin/code_reviewer.rs
 * High-Performance Native Rust Pre-Deployment Code Reviewer & Safety Auditor.
 */

use serde::{Deserialize, Serialize};
use std::env;
use std::error::Error;
use std::fs;
use std::path::{Path, PathBuf};
use std::process::Command;
use std::time::Instant;
use rayon::prelude::*;
use regex::Regex;

static SECRET_PATTERNS: &[(&str, &str)] = &[
    ("Google AI Studio API Key", r#"AIzaSy[A-Za-z0-9_-]{33}"#),
    ("Hugging Face User Token", r#"hf_[A-Za-z0-9]{34,}"#),
    ("Kaggle API Token", r#"kg_[A-Za-z0-9_-]{20,}"#),
    ("Doppler Service Token", r#"dp\.pt\.[A-Za-z0-9_-]{20,}"#),
    ("GitHub Personal Access Token", r#"ghp_[A-Za-z0-9]{36}"#),
    ("Docker Hub Personal Access Token", r#"dckr_pat_[A-Za-z0-9_-]{20,}"#),
    ("Grafana Cloud API Key", r#"glc_[A-Za-z0-9_-]{20,}"#),
    ("AWS Key", r#"AKIA[0-9A-Z]{16}"#),
    ("Private Key", r#"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----"#),
];

static EXCLUDED_DIR_PARTS: &[&str] = &[
    ".git", ".pytest_cache", ".ruff_cache", "__pycache__", "venv", ".venv",
    "node_modules", ".vercel", "target", "wandb"
];

static DUMMY_SUBSTRINGS: &[&str] = &["dummy", "replace", "example", "test_key", "your_api_key"];

#[derive(Serialize, Deserialize, Debug)]
struct SecretScanReport {
    scanned_files: usize,
    secret_leaks_found: usize,
    findings: Vec<String>,
    status: String,
}

#[derive(Serialize, Deserialize, Debug)]
struct KaggleAuditReport {
    issues_found: usize,
    issues: Vec<String>,
    status: String,
}

#[derive(Serialize, Deserialize, Debug)]
struct TestSuiteReport {
    passed: bool,
    exit_code: i32,
    summary: String,
    status: String,
}

#[derive(Serialize, Deserialize, Debug)]
struct FinalAuditReport {
    auditor: String,
    timestamp: String,
    overall_status: String,
    execution_time_ms: f64,
    secret_scan: SecretScanReport,
    kaggle_cuda_audit: KaggleAuditReport,
    test_suite: TestSuiteReport,
}

fn scan_secrets_rust(root: &Path) -> SecretScanReport {
    let mut files_to_scan = Vec::new();
    collect_files(root, &mut files_to_scan);
    let scanned_count = files_to_scan.len();

    let compiled_patterns: Vec<(&str, Regex)> = SECRET_PATTERNS
        .iter()
        .filter_map(|(name, pat)| Regex::new(pat).ok().map(|re| (*name, re)))
        .collect();

    let findings: Vec<String> = files_to_scan
        .par_iter()
        .flat_map(|file_path| {
            let mut local_findings = Vec::new();
            if let Ok(metadata) = fs::metadata(file_path) {
                if metadata.len() > 1_000_000 {
                    return local_findings;
                }
            }

            if let Ok(content) = fs::read_to_string(file_path) {
                for (name, re) in &compiled_patterns {
                    for m in re.find_iter(&content) {
                        let matched_str = m.as_str().to_lowercase();
                        if !DUMMY_SUBSTRINGS.iter().any(|d| matched_str.contains(d)) {
                            local_findings.push(format!(
                                "[SECRET LEAK] Found {} in {}",
                                name,
                                file_path.display()
                            ));
                            break;
                        }
                    }
                }
            }
            local_findings
        })
        .collect();

    let status = if findings.is_empty() { "PASSED".to_string() } else { "FAILED".to_string() };
    SecretScanReport {
        scanned_files: scanned_count,
        secret_leaks_found: findings.len(),
        findings,
        status,
    }
}

fn audit_kaggle_dependencies_rust(root: &Path) -> KaggleAuditReport {
    let manager_file = root.join("scripts").join("kaggle_notebook_manager.py");
    let mut issues = Vec::new();

    if manager_file.exists() {
        if let Ok(content) = fs::read_to_string(&manager_file) {
            let re = Regex::new(r#"pip['"]?,?\s*['"]install['"]?,?\s*['"]-q['"]?,?\s*['"]torch['"]"#).unwrap();
            if re.is_match(&content) {
                issues.push("Notebook setup reinstalls 'torch' on Kaggle, overwriting CUDA binaries.".to_string());
            }
        }
    }

    let status = if issues.is_empty() { "PASSED".to_string() } else { "WARNING".to_string() };
    KaggleAuditReport {
        issues_found: issues.len(),
        issues,
        status,
    }
}

fn run_test_suite_rust(root: &Path) -> TestSuiteReport {
    let start = Instant::now();
    let output = Command::new("python3")
        .args(["-m", "pytest", "-q", "--ignore=project/kaggle_kernel"])
        .current_dir(root)
        .output();

    match output {
        Ok(out) => {
            let exit_code = out.status.code().unwrap_or(-1);
            let passed = exit_code == 0;
            let stdout_str = String::from_utf8_lossy(&out.stdout);
            let summary = stdout_str.lines().last().unwrap_or("Tests executed").to_string();
            let status = if passed { "PASSED".to_string() } else { "FAILED".to_string() };
            println!("[INFO] Test Suite Output ({:.2}s): {}", start.elapsed().as_secs_f64(), summary);
            TestSuiteReport {
                passed,
                exit_code,
                summary,
                status,
            }
        }
        Err(e) => TestSuiteReport {
            passed: false,
            exit_code: -1,
            summary: format!("Execution Error: {}", e),
            status: "FAILED".to_string(),
        },
    }
}

fn collect_files(dir: &Path, file_list: &mut Vec<PathBuf>) {
    if let Ok(entries) = fs::read_dir(dir) {
        for entry in entries.flatten() {
            let path = entry.path();
            if let Some(file_name) = path.file_name().and_then(|n| n.to_str()) {
                if EXCLUDED_DIR_PARTS.contains(&file_name) || file_name.starts_with(".env") {
                    continue;
                }
            }
            if path.is_dir() {
                collect_files(&path, file_list);
            } else if path.is_file() {
                file_list.push(path);
            }
        }
    }
}

fn main() -> Result<(), Box<dyn Error>> {
    let start = Instant::now();
    println!("🔎 Running Pre-Deployment Code Review & Safety Audit (Rust Binary)...");

    let root_path = env::current_dir()?;

    let secret_report = scan_secrets_rust(&root_path);
    println!("⚡ [Rust Security Scanner] Scanned {} files in parallel via Rayon | Secret Leaks: {}", secret_report.scanned_files, secret_report.secret_leaks_found);

    let kaggle_report = audit_kaggle_dependencies_rust(&root_path);
    println!("📦 [Kaggle CUDA Audit] Issues Found: {}", kaggle_report.issues_found);

    let test_report = run_test_suite_rust(&root_path);

    let all_passed = secret_report.status == "PASSED"
        && test_report.status == "PASSED"
        && kaggle_report.status != "FAILED";

    let overall_status = if all_passed { "READY_FOR_PROD".to_string() } else { "BLOCKED".to_string() };
    let elapsed_ms = start.elapsed().as_secs_f64() * 1000.0;

    let final_report = FinalAuditReport {
        auditor: "RustCodeReviewer v1.0".to_string(),
        timestamp: chrono::Utc::now().to_rfc3339(),
        overall_status: overall_status.clone(),
        execution_time_ms: elapsed_ms,
        secret_scan: secret_report,
        kaggle_cuda_audit: kaggle_report,
        test_suite: test_report,
    };

    println!("\n============================================================");
    println!("📊 AUDIT COMPLETE — OVERALL STATUS: {}", overall_status);
    println!("============================================================");

    let json_output = serde_json::to_string_pretty(&final_report)?;
    println!("{}", json_output);

    if overall_status == "READY_FOR_PROD" {
        Ok(())
    } else {
        Err("Code review safety audit blocked deployment".into())
    }
}
