/*!
 * rust_core/src/security_audit.rs
 * High-performance Parallel Rust Security Auditor & Secret Leakage Scanner.
 * Scans codebase files in parallel via Rayon, ignoring dummy keys and vendor directories.
 */

use pyo3::prelude::*;
use std::fs;
use std::path::{Path, PathBuf};
use rayon::prelude::*;
use regex::Regex;

static SECRET_PATTERNS: &[(&str, &str)] = &[
    ("Google AI Studio API Key", r#"AIzaSy[A-Za-z0-9_-]{33}"#),
    ("Hugging Face User Token", r#"hf_[A-Za-z0-9]{34,}"#),
    ("Kaggle API Token", r#"kg_[A-Za-z0-9_-]{20,}"#),
    ("Doppler Service Token", r#"dp\.pt\.[A-Za-z0-9_-]{20,}"#),
    ("GitHub Personal Access Token", r#"ghp_[A-Za-z0-9]{36}"#),
    ("Grafana Cloud API Key", r#"glc_[A-Za-z0-9_-]{20,}"#),
    ("AWS Key", r#"AKIA[0-9A-Z]{16}"#),
    ("Private Key", r#"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----"#),
];

static EXCLUDED_DIR_PARTS: &[&str] = &[
    ".git", ".pytest_cache", ".ruff_cache", "__pycache__", "venv", ".venv",
    "node_modules", ".vercel", "target", "wandb"
];

static DUMMY_SUBSTRINGS: &[&str] = &["dummy", "replace", "example", "test_key", "your_api_key"];

#[derive(serde::Serialize, serde::Deserialize, Debug)]
pub struct AuditReport {
    pub scanned_files: usize,
    pub secret_leaks_found: usize,
    pub findings: Vec<String>,
    pub status: String,
}

pub fn scan_directory_secrets_rust(root_path: &str) -> Result<(bool, usize, Vec<String>), String> {
    let root = Path::new(root_path);
    if !root.exists() {
        return Ok((false, 0, vec!["Root path does not exist".to_string()]));
    }

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
                        let is_dummy = DUMMY_SUBSTRINGS.iter().any(|d| matched_str.contains(d));
                        if !is_dummy {
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

    let passed = findings.is_empty();
    Ok((passed, scanned_count, findings))
}

/// Run parallel security audit and secret leak scanning over target directory.
#[pyfunction]
pub fn run_rust_security_audit(py: Python<'_>, root_path: &str) -> PyResult<(bool, usize, Vec<String>)> {
    let root_path_owned = root_path.to_owned();
    let result = py.allow_threads(move || {
        scan_directory_secrets_rust(&root_path_owned).unwrap_or((false, 0, vec!["Scan failed".to_string()]))
    });
    Ok(result)
}

fn collect_files(dir: &Path, file_list: &mut Vec<PathBuf>) {
    if let Ok(entries) = fs::read_dir(dir) {
        for entry in entries.flatten() {
            let path = entry.path();
            if let Some(file_name) = path.file_name().and_then(|n| n.to_str()) {
                if EXCLUDED_DIR_PARTS.contains(&file_name) {
                    continue;
                }
                if file_name.starts_with(".env") {
                    continue; // Skip local gitignored .env files
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
