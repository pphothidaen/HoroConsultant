//! build.rs — Auto-generate Rust routing table from Python FastAPI route definitions.
//!
//! KAN-71: Eliminates manual synchronization between Python routes and Rust gateway.
//!
//! This script parses:
//!   1. `project/main.py` — include_router() calls with prefixes
//!   2. `project/routers/*.py` — @router.get/post/delete/... decorators
//!
//! It generates `src/generated_routes.rs` containing:
//!   - A static array of (method, path) tuples for all Python-proxied routes
//!   - Dynamic prefix patterns for parameterized routes
//!
//! The generated file is included by `server.rs` via `include!()`.

use std::collections::BTreeMap;
use std::env;
use std::fs;
use std::path::{Path, PathBuf};

fn main() {
    let manifest_dir = env::var("CARGO_MANIFEST_DIR").expect("CARGO_MANIFEST_DIR not set");
    let crate_root = PathBuf::from(&manifest_dir);
    let repo_root = crate_root
        .parent()
        .expect("rust_core must be a subdirectory of the repo root")
        .to_path_buf();

    let main_py = repo_root.join("project/main.py");
    let output_path = crate_root.join("src/generated_routes.rs");

    println!("cargo:rerun-if-changed={}", main_py.display());

    let routes = collect_routes(&main_py, &repo_root);
    let generated = generate_rust_source(&routes);

    fs::write(&output_path, generated).unwrap_or_else(|e| {
        panic!(
            "Failed to write generated routes to {}: {}",
            output_path.display(),
            e
        )
    });

    println!(
        "cargo:warning=KAN-71: Generated {} routes from Python definitions",
        routes.len()
    );
}

// ── Data Model ──────────────────────────────────────────────────────────────

#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord)]
struct Route {
    method: String,
    path: String,
    /// True if this route has path parameters (e.g. /api/jira/tickets/{id})
    has_params: bool,
    /// The prefix for dynamic matching (e.g. /api/jira/tickets/)
    dynamic_prefix: Option<String>,
}

// ── Route Collection ────────────────────────────────────────────────────────

fn collect_routes(main_py: &Path, repo_root: &Path) -> Vec<Route> {
    let mut routes = Vec::new();

    // 1. Parse main.py for include_router() calls with prefixes
    let main_source = fs::read_to_string(main_py)
        .unwrap_or_else(|e| panic!("Failed to read {}: {}", main_py.display(), e));

    let router_prefixes = parse_include_routers(&main_source);
    let import_map = parse_import_routers(&main_source, repo_root);

    // 2. Parse each router file for @router.method() decorators using import map
    let router_files: Vec<(String, PathBuf)> = import_map.into_iter().collect();

    for (router_name, file_path) in &router_files {
        let source = fs::read_to_string(file_path)
            .unwrap_or_else(|e| panic!("Failed to read {}: {}", file_path.display(), e));

        let router_prefix = router_prefixes
            .get(router_name.as_str())
            .cloned()
            .unwrap_or_default();

        let file_routes = parse_route_decorators(&source, &router_prefix);
        routes.extend(file_routes);
    }

    // 3. Add routes defined directly in main.py (not via include_router)
    let main_routes = parse_route_decorators(&main_source, "");
    routes.extend(main_routes);

    // 4. Add native Rust routes (these are always present)
    routes.extend(native_rust_routes());

    // Deduplicate and sort
    routes.sort();
    routes.dedup();

    routes
}

fn parse_include_routers(source: &str) -> BTreeMap<String, String> {
    let mut result = BTreeMap::new();

    // Match patterns like:
    //   app.include_router(v2_router, prefix="/api/v2")
    //   app.include_router(admin_router)
    let lines: Vec<&str> = source.lines().collect();
    for line in &lines {
        let trimmed = line.trim();
        if trimmed.starts_with("app.include_router(") {
            // Extract router name and optional prefix
            let content = trimmed
                .trim_start_matches("app.include_router(")
                .trim_end_matches(')');

            let parts: Vec<&str> = content.split(',').map(|s| s.trim()).collect();
            if parts.is_empty() {
                continue;
            }

            let router_name = parts[0].to_string();
            let prefix = parts
                .iter()
                .skip(1)
                .find_map(|p| {
                    p.strip_prefix("prefix=")
                        .and_then(|v| v.trim_matches('"').to_string().into())
                })
                .unwrap_or_default();

            result.insert(router_name, prefix);
        }
    }

    result
}

/// Parse import statements to build a mapping from router variable name to file path
/// e.g., "from project.routers.mlops import mlops_router" -> ("mlops_router", "project/routers/mlops.py")
/// e.g., "from project.routers.chat import router as chat_router" -> ("chat_router", "project/routers/chat.py")
/// e.g., "from project.routers import astrology_router, debate_router" -> ("astrology_router", "project/routers/astrology.py")
fn parse_import_routers(source: &str, repo_root: &Path) -> BTreeMap<String, PathBuf> {
    let mut result = BTreeMap::new();

    for line in source.lines() {
        let trimmed = line.trim();
        if trimmed.starts_with("from project.") && trimmed.contains(" import ") {
            // Parse: from project.routers.mlops import mlops_router
            // or: from project.routers.chat import router as chat_router
            // or: from project.routers import astrology_router, debate_router
            let after_from = trimmed.trim_start_matches("from ");
            let parts: Vec<&str> = after_from.splitn(2, " import ").collect();
            if parts.len() != 2 {
                continue;
            }

            let module_path = parts[0].trim();
            let import_part = parts[1].trim();

            // Convert module path to file path
            // project.routers.mlops -> project/routers/mlops.py
            // project.admin_router -> project/admin_router.py
            // project.routers -> project/routers/ (package, need to find individual files)
            let file_path = module_path.replace('.', "/");
            let full_path = repo_root.join(&file_path).with_extension("py");

            if full_path.exists() {
                // Single file import
                for import_item in import_part.split(',') {
                    let import_item = import_item.trim();
                    let var_name = if let Some(alias_pos) = import_item.find(" as ") {
                        import_item[alias_pos + 4..].trim().to_string()
                    } else {
                        import_item.trim().to_string()
                    };

                    if var_name.contains("router") {
                        result.insert(var_name, full_path.clone());
                    }
                }
            } else {
                // Package import (e.g., from project.routers import astrology_router)
                // Try to find individual files in the package directory
                let package_dir = repo_root.join(&file_path);
                if package_dir.is_dir() {
                    for import_item in import_part.split(',') {
                        let import_item = import_item.trim();
                        let var_name = if let Some(alias_pos) = import_item.find(" as ") {
                            import_item[alias_pos + 4..].trim().to_string()
                        } else {
                            import_item.trim().to_string()
                        };

                        if var_name.contains("router") {
                            // Try to find the file: astrology_router -> astrology.py
                            let file_stem = var_name.replace("_router", "");
                            let candidate = package_dir.join(&file_stem).with_extension("py");
                            if candidate.exists() {
                                result.insert(var_name, candidate);
                            }
                        }
                    }
                }
            }
        }
    }

    result
}

fn parse_route_decorators(source: &str, router_prefix: &str) -> Vec<Route> {
    let mut routes = Vec::new();

    // Match patterns like:
    //   @router.get("/path")
    //   @astrology_router.post("/path")
    //   @v2_router.get("/path/{param}")
    //   @app.get("/path")
    //   @app.post("/path", include_in_schema=False)
    let method_pattern = regex_lite::Regex::new(
        r#"@(\w+_router|router|app)\.(get|post|put|delete|patch|head|options)\("([^"]+)"#,
    )
    .expect("valid regex");

    for caps in method_pattern.captures_iter(source) {
        let method = caps.get(2).unwrap().to_uppercase();
        let raw_path = caps.get(3).unwrap();

        let full_path = if router_prefix.is_empty() {
            raw_path.to_string()
        } else {
            format!("{}{}", router_prefix, raw_path)
        };

        let (normalized_path, has_params, dynamic_prefix) = normalize_path(&full_path);

        routes.push(Route {
            method,
            path: normalized_path,
            has_params,
            dynamic_prefix,
        });
    }

    routes
}

fn normalize_path(path: &str) -> (String, bool, Option<String>) {
    // Check for path parameters like {id}
    if path.contains('{') {
        // Extract the prefix before the first parameter
        let param_start = path.find('{').unwrap();
        let prefix = &path[..param_start];
        // Remove trailing slash for the prefix
        let dynamic_prefix = prefix.trim_end_matches('/').to_string();
        (path.to_string(), true, Some(dynamic_prefix))
    } else {
        (path.to_string(), false, None)
    }
}

fn native_rust_routes() -> Vec<Route> {
    // These routes are handled natively in Rust, not proxied to Python
    vec![
        Route {
            method: "GET".to_string(),
            path: "/health".to_string(),
            has_params: false,
            dynamic_prefix: None,
        },
        Route {
            method: "GET".to_string(),
            path: "/api/v1/health".to_string(),
            has_params: false,
            dynamic_prefix: None,
        },
        Route {
            method: "POST".to_string(),
            path: "/api/v1/bazi/calculate".to_string(),
            has_params: false,
            dynamic_prefix: None,
        },
        Route {
            method: "GET".to_string(),
            path: "/api/v1/eot".to_string(),
            has_params: false,
            dynamic_prefix: None,
        },
    ]
}

// ── Code Generation ─────────────────────────────────────────────────────────

fn generate_rust_source(routes: &[Route]) -> String {
    let mut output = String::new();

    output.push_str("// AUTO-GENERATED by build.rs — DO NOT EDIT\n");
    output.push_str("// KAN-71: Generated from Python FastAPI route definitions\n");
    output.push_str("//\n");
    output.push_str("// This file is regenerated on every build. To modify routes,\n");
    output.push_str("// edit the Python router files in project/routers/ or project/main.py\n\n");

    // Generate static routes array
    output.push_str("/// Static routes that can be matched exactly\n");
    output.push_str("pub static STATIC_ROUTES: &[(&str, &str)] = &[\n");

    for route in routes {
        if !route.has_params {
            output.push_str(&format!(
                "    (\"{}\", \"{}\"),\n",
                route.method, route.path
            ));
        }
    }

    output.push_str("];\n\n");

    // Generate dynamic prefix patterns
    output.push_str("/// Dynamic route prefixes for parameterized routes\n");
    output.push_str("pub static DYNAMIC_PREFIXES: &[(&str, &str)] = &[\n");

    for route in routes {
        if let Some(ref prefix) = route.dynamic_prefix {
            output.push_str(&format!("    (\"{}\", \"{}\"),\n", route.method, prefix));
        }
    }

    output.push_str("];\n\n");

    // Generate the route matching function
    output.push_str("/// Check if a (method, path) pair matches any Python-proxied route\n");
    output.push_str("pub fn is_python_proxy_route(method: &str, path: &str) -> bool {\n");
    output.push_str("    // Check static routes first\n");
    output.push_str("    if STATIC_ROUTES.iter().any(|(m, p)| *m == method && *p == path) {\n");
    output.push_str("        return true;\n");
    output.push_str("    }\n");
    output.push_str("    \n");
    output.push_str("    // Check dynamic prefixes\n");
    output.push_str("    DYNAMIC_PREFIXES.iter().any(|(m, prefix)| {\n");
    output.push_str("        *m == method && path.starts_with(prefix)\n");
    output.push_str("    })\n");
    output.push_str("}\n");

    output
}

// ── Minimal regex implementation (no external deps) ─────────────────────────

mod regex_lite {
    pub struct Regex {
        pattern: String,
    }

    impl Regex {
        pub fn new(pattern: &str) -> Result<Self, String> {
            Ok(Self {
                pattern: pattern.to_string(),
            })
        }

        pub fn captures_iter<'a>(
            &'a self,
            text: &'a str,
        ) -> impl Iterator<Item = Captures<'a>> + 'a {
            let mut results = Vec::new();
            let _pattern = &self.pattern;

            // Simple pattern matching for @(router|app).METHOD("path")
            // Only attempt matches at valid UTF-8 char boundaries
            for (i, _) in text.char_indices() {
                if let Some(caps) = try_match_at(text, i) {
                    results.push(caps.0);
                }
            }

            results.into_iter()
        }
    }

    #[allow(dead_code)]
    pub struct Captures<'a>(Vec<Option<&'a str>>, usize);

    impl<'a> Captures<'a> {
        pub fn get(&self, index: usize) -> Option<&'a str> {
            self.0.get(index).and_then(|o| o.map(|s| s))
        }
    }

    fn try_match_at(text: &str, start: usize) -> Option<(Captures<'_>, usize)> {
        let bytes = text.as_bytes();
        let len = bytes.len();

        // Look for @<name>. where <name> ends with _router or is "router" or "app"
        if start >= len || bytes[start] != b'@' {
            return None;
        }

        // Find the dot after the router variable name
        let after_at = &text[start + 1..];
        let dot_pos = after_at.find('.')?;
        if !after_at.is_char_boundary(dot_pos) {
            return None;
        }
        let router_var = &after_at[..dot_pos];

        // Check if it's a valid router variable name
        let is_valid_router = router_var == "router"
            || router_var == "app"
            || (router_var.ends_with("_router") && router_var.len() > 7);
        if !is_valid_router {
            return None;
        }

        // Extract method name
        let after_dot = &after_at[dot_pos + 1..];
        let method_end = after_dot.find('(')?;
        if !after_dot.is_char_boundary(method_end) {
            return None;
        }
        let method = &after_dot[..method_end];

        // Check if it's a valid HTTP method
        let valid_methods = ["get", "post", "put", "delete", "patch", "head", "options"];
        if !valid_methods.contains(&method.to_lowercase().as_str()) {
            return None;
        }

        // Find the quoted path
        let after_method = &after_dot[method_end + 1..];
        let quote_start = after_method.find('"')?;
        if !after_method.is_char_boundary(quote_start) {
            return None;
        }
        let after_quote = &after_method[quote_start + 1..];
        let quote_end = after_quote.find('"')?;
        if !after_quote.is_char_boundary(quote_end) {
            return None;
        }
        let path = &after_quote[..quote_end];

        let end_pos = start + 1 + dot_pos + 1 + method_end + 1 + quote_start + 1 + quote_end + 1;

        Some((
            Captures(
                vec![
                    None, // full match (unused)
                    Some(router_var),
                    Some(method),
                    Some(path),
                ],
                end_pos,
            ),
            end_pos,
        ))
    }
}
