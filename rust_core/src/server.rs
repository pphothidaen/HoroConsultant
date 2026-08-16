/*!
 * rust_core/src/server.rs
 * Contract-safe Axum gateway for the Rust-first production runtime.
 *
 * Only parity-qualified BaZi, true-solar-time, and health requests execute in
 * Rust. Every retained Python route is matched against a closed allowlist and
 * forwarded byte-for-byte to the localhost Uvicorn worker.
 */

#[cfg(feature = "python")]
use pyo3::prelude::*;

use axum::{
    body::{to_bytes, Body, Bytes},
    extract::State,
    http::{
        header::{self, HeaderName, HeaderValue},
        HeaderMap, Method, Request, Response, StatusCode,
    },
    routing::any,
    Router,
};
use chrono::{Datelike, NaiveDate, NaiveDateTime, Timelike};
use reqwest::Client;
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::{
    collections::HashSet,
    net::SocketAddr,
    sync::{
        atomic::{AtomicU64, Ordering},
        Arc,
    },
    time::{Duration, SystemTime, UNIX_EPOCH},
};

const DEFAULT_MAX_BODY_BYTES: usize = 2 * 1024 * 1024;
const DEFAULT_PROXY_TIMEOUT: Duration = Duration::from_secs(30);
const CORRELATION_HEADER: &str = "x-request-id";
const INTERNAL_BAZI_RENDER_PATH: &str = "/_internal/v1/bazi/render";

/// Runtime configuration for a gateway instance.
#[derive(Clone, Debug)]
pub struct GatewayConfig {
    python_origin: String,
    max_body_bytes: usize,
    proxy_timeout: Duration,
    allowed_origins: Vec<String>,
}

impl GatewayConfig {
    /// Create a gateway targeting a loopback-only Python worker.
    pub fn new(python_origin: String) -> Self {
        let normalized = python_origin.trim_end_matches('/').to_string();
        let parsed = reqwest::Url::parse(&normalized).expect("valid Python worker origin");
        assert!(
            matches!(parsed.host_str(), Some("127.0.0.1" | "localhost" | "::1")),
            "Python worker origin must be loopback-only"
        );
        let allowed_origins = std::env::var("CORS_ALLOWED_ORIGINS")
            .ok()
            .map(|raw| {
                raw.split(',')
                    .map(str::trim)
                    .filter(|origin| !origin.is_empty())
                    .map(ToOwned::to_owned)
                    .collect::<Vec<_>>()
            })
            .filter(|origins| !origins.is_empty())
            .unwrap_or_else(|| vec!["*".to_string()]);
        Self {
            python_origin: normalized,
            max_body_bytes: DEFAULT_MAX_BODY_BYTES,
            proxy_timeout: DEFAULT_PROXY_TIMEOUT,
            allowed_origins,
        }
    }

    pub fn with_max_body_bytes(mut self, max_body_bytes: usize) -> Self {
        self.max_body_bytes = max_body_bytes;
        self
    }

    pub fn with_proxy_timeout(mut self, proxy_timeout: Duration) -> Self {
        self.proxy_timeout = proxy_timeout;
        self
    }

    pub fn with_allowed_origins(mut self, allowed_origins: Vec<String>) -> Self {
        self.allowed_origins = allowed_origins;
        self
    }
}

#[derive(Clone)]
struct AppState {
    client: Client,
    config: GatewayConfig,
    correlation_sequence: Arc<AtomicU64>,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
enum RouteKind {
    Liveness,
    Readiness,
    NativeBazi,
    NativeEquationOfTime,
    PythonProxy,
}

#[derive(Debug, Deserialize)]
struct PublicBaziRequest {
    birth_datetime: String,
    longitude: f64,
    utc_offset_hours: f64,
    #[serde(default)]
    unknown_hour: bool,
}

#[derive(Debug, Deserialize)]
struct RenderedBaziAssets {
    svg_content: String,
    zodiac_svg: String,
}

#[derive(Debug, Serialize)]
struct RuntimeBackend {
    rust_available: bool,
    rust_version: &'static str,
    active_kernels: [&'static str; 2],
}

/// Build the public gateway router. The fallback is deliberate: every target
/// is checked by `route_kind` before any network request can leave Axum.
pub fn build_gateway(config: GatewayConfig) -> Router {
    let client = Client::builder()
        .connect_timeout(config.proxy_timeout)
        .build()
        .expect("build localhost proxy client");
    let state = AppState {
        client,
        config,
        correlation_sequence: Arc::new(AtomicU64::new(0)),
    };
    Router::new()
        .fallback(any(gateway_handler))
        .with_state(state)
}

async fn gateway_handler(State(state): State<AppState>, request: Request<Body>) -> Response<Body> {
    let request_headers = request.headers().clone();
    let correlation_id = correlation_id(&state, &request_headers);
    let origin = request_headers
        .get(header::ORIGIN)
        .and_then(|value| value.to_str().ok())
        .map(ToOwned::to_owned);
    let method = request.method().clone();
    let uri = request.uri().clone();

    if method == Method::OPTIONS && request_headers.contains_key("access-control-request-method") {
        let requested_method = request_headers
            .get("access-control-request-method")
            .and_then(|value| value.to_str().ok())
            .and_then(|value| Method::from_bytes(value.as_bytes()).ok());
        let response = match requested_method {
            Some(requested) if route_kind(&requested, uri.path()).is_some() => {
                cors_preflight(&state.config, &request_headers)
            }
            _ => not_found(),
        };
        return finish_response(response, &state.config, origin.as_deref(), &correlation_id);
    }

    let Some(kind) = route_kind(&method, uri.path()) else {
        let response = if path_is_known(uri.path()) {
            json_response(
                StatusCode::METHOD_NOT_ALLOWED,
                json!({"detail": "Method Not Allowed"}),
            )
        } else {
            not_found()
        };
        return finish_response(response, &state.config, origin.as_deref(), &correlation_id);
    };

    if request_body_is_too_large(&request_headers, state.config.max_body_bytes) {
        return finish_response(
            payload_too_large(),
            &state.config,
            origin.as_deref(),
            &correlation_id,
        );
    }

    let (parts, body) = request.into_parts();
    let body = match to_bytes(body, state.config.max_body_bytes).await {
        Ok(body) => body,
        Err(_) => {
            return finish_response(
                payload_too_large(),
                &state.config,
                origin.as_deref(),
                &correlation_id,
            )
        }
    };

    let response = match kind {
        RouteKind::Liveness => liveness_response(),
        RouteKind::Readiness => readiness_response(),
        RouteKind::NativeEquationOfTime => {
            native_equation_of_time(&state, &parts, body, &correlation_id).await
        }
        RouteKind::NativeBazi => native_bazi(&state, &parts, body, &correlation_id).await,
        RouteKind::PythonProxy => proxy_request(&state, &parts, body, &correlation_id).await,
    };
    finish_response(response, &state.config, origin.as_deref(), &correlation_id)
}

fn route_kind(method: &Method, path: &str) -> Option<RouteKind> {
    match (method, path) {
        (&Method::GET, "/health") => Some(RouteKind::Liveness),
        (&Method::GET, "/api/v1/health") => Some(RouteKind::Readiness),
        (&Method::POST, "/api/v1/bazi/calculate") => Some(RouteKind::NativeBazi),
        (&Method::GET, "/api/v1/eot") => Some(RouteKind::NativeEquationOfTime),

        (&Method::POST, "/admin/auth/google")
        | (&Method::GET, "/admin/auth/config")
        | (&Method::GET, "/admin/catalog")
        | (&Method::GET, "/admin/catalog/summary")
        | (&Method::GET, "/admin/grayzone")
        | (&Method::POST, "/admin/grayzone/answer")
        | (&Method::DELETE, "/admin/grayzone/answer")
        | (&Method::GET, "/admin/finetune/status")
        | (&Method::POST, "/admin/finetune/export-grayzone")
        | (&Method::POST, "/admin/finetune/merge")
        | (&Method::POST, "/admin/finetune/trigger")
        | (&Method::GET, "/admin/finetune/download")
        | (&Method::GET, "/admin/finetune/download-grayzone")
        | (&Method::GET, "/admin/code-review")
        | (&Method::GET, "/hitl/queue")
        | (&Method::GET, "/hitl/stats")
        | (&Method::GET, "/hitl/export")
        | (&Method::POST, "/hitl/batch-draft")
        | (&Method::GET, "/api/v1/ziwei/calculate")
        | (&Method::GET, "/api/v1/qimen/calculate")
        | (&Method::GET, "/api/v1/liuren/calculate")
        | (&Method::GET, "/api/v1/iching/calculate")
        | (&Method::GET, "/api/v1/xuankong/calculate")
        | (&Method::GET, "/api/v1/zeji/calculate")
        | (&Method::GET, "/api/v1/thaivedic/calculate")
        | (&Method::GET, "/api/v1/western/calculate")
        | (&Method::GET, "/api/v1/numerology/calculate")
        | (&Method::POST, "/api/v1/location/resolve")
        | (&Method::POST, "/bazi/interpret")
        | (&Method::POST, "/v1/bazi/interpret")
        | (&Method::POST, "/api/v1/bazi/interpret")
        | (&Method::POST, "/api/v1/bazi/validate")
        | (&Method::GET, "/")
        | (&Method::GET, "/admin")
        | (&Method::GET, "/hitl-studio")
        | (&Method::GET, "/app.js")
        | (&Method::GET, "/style.css")
        | (&Method::GET, "/docs")
        | (&Method::HEAD, "/docs")
        | (&Method::GET, "/docs/oauth2-redirect")
        | (&Method::HEAD, "/docs/oauth2-redirect")
        | (&Method::GET, "/redoc")
        | (&Method::HEAD, "/redoc")
        | (&Method::GET, "/openapi.json")
        | (&Method::HEAD, "/openapi.json")
        | (&Method::GET, "/metrics")
        | (&Method::GET, "/metrics/seed-dummy")
        | (&Method::POST, "/metrics/seed-dummy")
        | (&Method::GET, "/api/health") => Some(RouteKind::PythonProxy),
        (&Method::GET, dynamic) | (&Method::HEAD, dynamic) if dynamic.starts_with("/static/") => {
            Some(RouteKind::PythonProxy)
        }
        (&Method::GET, dynamic) if one_segment_after(dynamic, "/admin/catalog/source/") => {
            Some(RouteKind::PythonProxy)
        }
        (&Method::GET, dynamic) if one_segment_after(dynamic, "/hitl/item/") => {
            Some(RouteKind::PythonProxy)
        }
        (&Method::POST, dynamic) if one_segment_after(dynamic, "/hitl/draft/") => {
            Some(RouteKind::PythonProxy)
        }
        (&Method::POST, dynamic) | (&Method::DELETE, dynamic)
            if one_segment_after(dynamic, "/hitl/review/") =>
        {
            Some(RouteKind::PythonProxy)
        }
        _ => None,
    }
}

fn one_segment_after(path: &str, prefix: &str) -> bool {
    path.strip_prefix(prefix)
        .is_some_and(|segment| !segment.is_empty() && !segment.contains('/'))
}

fn path_is_known(path: &str) -> bool {
    [Method::GET, Method::POST, Method::DELETE, Method::HEAD]
        .iter()
        .any(|method| route_kind(method, path).is_some())
}

fn liveness_response() -> Response<Body> {
    json_response(
        StatusCode::OK,
        json!({
            "status": "ok",
            "service": "Computational Metaphysics Engine",
        }),
    )
}

fn readiness_response() -> Response<Body> {
    let backend = RuntimeBackend {
        rust_available: true,
        rust_version: env!("CARGO_PKG_VERSION"),
        active_kernels: ["calculate_bazi", "calculate_true_solar_time"],
    };
    let commit = option_env!("GIT_COMMIT_HASH").unwrap_or("unknown");
    json_response(
        StatusCode::OK,
        json!({
            "status": "ok",
            "service": "Computational Metaphysics Engine",
            "version": format!("1.0.0.{commit}"),
            "git_commit": commit,
            "gateway": "rust_axum",
            "python_worker": "ready",
            "runtime_backend": backend,
        }),
    )
}

async fn native_equation_of_time(
    state: &AppState,
    parts: &axum::http::request::Parts,
    body: Bytes,
    correlation_id: &str,
) -> Response<Body> {
    let date = reqwest::Url::parse(&format!("http://localhost{}", parts.uri))
        .ok()
        .and_then(|url| {
            url.query_pairs()
                .filter(|(key, _)| key == "date")
                .map(|(_, value)| value.into_owned())
                .last()
        });
    let Some(date) = date else {
        return proxy_request(state, parts, body, correlation_id).await;
    };
    let Ok(parsed) = NaiveDate::parse_from_str(&date, "%Y-%m-%d") else {
        return json_response(
            StatusCode::UNPROCESSABLE_ENTITY,
            json!({"detail": "Invalid date format, use YYYY-MM-DD"}),
        );
    };
    let Some(datetime) = parsed.and_hms_opt(0, 0, 0) else {
        return json_response(
            StatusCode::UNPROCESSABLE_ENTITY,
            json!({"detail": "Invalid date format, use YYYY-MM-DD"}),
        );
    };
    json_response(
        StatusCode::OK,
        json!({
            "date": date,
            "eot_minutes": crate::solar::calculate_equation_of_time(datetime),
        }),
    )
}

async fn native_bazi(
    state: &AppState,
    parts: &axum::http::request::Parts,
    body: Bytes,
    correlation_id: &str,
) -> Response<Body> {
    let Ok(public_request) = serde_json::from_slice::<PublicBaziRequest>(&body) else {
        return proxy_request(state, parts, body, correlation_id).await;
    };
    let Ok(datetime) =
        NaiveDateTime::parse_from_str(&public_request.birth_datetime, "%Y-%m-%d %H:%M:%S")
    else {
        return proxy_request(state, parts, body, correlation_id).await;
    };
    let input = crate::bazi::BaziInput {
        year: datetime.date().year(),
        month: datetime.date().month(),
        day: datetime.date().day(),
        hour: datetime.time().hour(),
        minute: datetime.time().minute(),
        second: datetime.time().second(),
        longitude: public_request.longitude,
        utc_offset_hours: public_request.utc_offset_hours,
        unknown_hour: public_request.unknown_hour,
    };
    let Ok(chart) = crate::bazi::calculate_bazi(&input) else {
        return proxy_request(state, parts, body, correlation_id).await;
    };
    let Ok(chart_body) = serde_json::to_vec(&chart) else {
        return bad_gateway(correlation_id);
    };
    let render_url = format!(
        "{}{}",
        state.config.python_origin, INTERNAL_BAZI_RENDER_PATH
    );
    let render_request = state
        .client
        .post(render_url)
        .header(header::CONTENT_TYPE, "application/json")
        .header(CORRELATION_HEADER, correlation_id)
        .body(chart_body)
        .send();
    let render_response =
        match tokio::time::timeout(state.config.proxy_timeout, render_request).await {
            Ok(Ok(response)) if response.status() == StatusCode::OK => response,
            Ok(Ok(_)) | Ok(Err(_)) => return bad_gateway(correlation_id),
            Err(_) => return gateway_timeout(correlation_id),
        };
    let assets = match tokio::time::timeout(
        state.config.proxy_timeout,
        render_response.json::<RenderedBaziAssets>(),
    )
    .await
    {
        Ok(Ok(assets)) => assets,
        Ok(Err(_)) => return bad_gateway(correlation_id),
        Err(_) => return gateway_timeout(correlation_id),
    };
    let Ok(mut response) = serde_json::to_value(chart) else {
        return bad_gateway(correlation_id);
    };
    let Some(response_object) = response.as_object_mut() else {
        return bad_gateway(correlation_id);
    };
    response_object.insert("svg_content".to_string(), Value::String(assets.svg_content));
    response_object.insert("zodiac_svg".to_string(), Value::String(assets.zodiac_svg));
    json_response(StatusCode::OK, response)
}

async fn proxy_request(
    state: &AppState,
    parts: &axum::http::request::Parts,
    body: Bytes,
    correlation_id: &str,
) -> Response<Body> {
    let target = format!("{}{}", state.config.python_origin, parts.uri);
    let excluded = connection_header_names(&parts.headers);
    let mut request = state.client.request(parts.method.clone(), target);
    for (name, value) in &parts.headers {
        if should_forward_request_header(name, &excluded) {
            request = request.header(name, value);
        }
    }
    request = request
        .header(CORRELATION_HEADER, correlation_id)
        .body(body);

    let upstream = match tokio::time::timeout(state.config.proxy_timeout, request.send()).await {
        Ok(Ok(response)) => response,
        Ok(Err(error)) if error.is_timeout() => return gateway_timeout(correlation_id),
        Ok(Err(_)) => return bad_gateway(correlation_id),
        Err(_) => return gateway_timeout(correlation_id),
    };
    let status = upstream.status();
    let response_headers = upstream.headers().clone();
    let response_body =
        match tokio::time::timeout(state.config.proxy_timeout, upstream.bytes()).await {
            Ok(Ok(bytes)) => bytes,
            Ok(Err(_)) => return bad_gateway(correlation_id),
            Err(_) => return gateway_timeout(correlation_id),
        };
    let excluded = connection_header_names(&response_headers);
    let mut response = Response::new(Body::from(response_body));
    *response.status_mut() = status;
    for (name, value) in &response_headers {
        if should_forward_response_header(name, &excluded) {
            response.headers_mut().append(name, value.clone());
        }
    }
    response
}

fn connection_header_names(headers: &HeaderMap) -> HashSet<HeaderName> {
    headers
        .get_all(header::CONNECTION)
        .iter()
        .filter_map(|value| value.to_str().ok())
        .flat_map(|value| value.split(','))
        .filter_map(|name| HeaderName::from_bytes(name.trim().as_bytes()).ok())
        .collect()
}

fn is_hop_by_hop(name: &HeaderName) -> bool {
    matches!(
        name.as_str(),
        "connection"
            | "keep-alive"
            | "proxy-authenticate"
            | "proxy-authorization"
            | "te"
            | "trailer"
            | "transfer-encoding"
            | "upgrade"
    )
}

fn should_forward_request_header(name: &HeaderName, excluded: &HashSet<HeaderName>) -> bool {
    !is_hop_by_hop(name)
        && !excluded.contains(name)
        && name != header::HOST
        && name != header::CONTENT_LENGTH
        && name.as_str() != CORRELATION_HEADER
}

fn should_forward_response_header(name: &HeaderName, excluded: &HashSet<HeaderName>) -> bool {
    !is_hop_by_hop(name)
        && !excluded.contains(name)
        && name != header::CONTENT_LENGTH
        && name.as_str() != CORRELATION_HEADER
}

fn correlation_id(state: &AppState, headers: &HeaderMap) -> String {
    if let Some(existing) = headers
        .get(CORRELATION_HEADER)
        .and_then(|value| value.to_str().ok())
        .filter(|value| !value.trim().is_empty())
    {
        return existing.to_string();
    }
    let sequence = state.correlation_sequence.fetch_add(1, Ordering::Relaxed);
    let timestamp = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_nanos();
    format!("horo-{timestamp:x}-{sequence:x}")
}

fn finish_response(
    mut response: Response<Body>,
    config: &GatewayConfig,
    origin: Option<&str>,
    correlation_id: &str,
) -> Response<Body> {
    response.headers_mut().insert(
        HeaderName::from_static(CORRELATION_HEADER),
        HeaderValue::from_str(correlation_id).expect("request correlation ID is a valid header"),
    );
    apply_cors(response.headers_mut(), config, origin);
    response
}

fn apply_cors(headers: &mut HeaderMap, config: &GatewayConfig, origin: Option<&str>) {
    let Some(origin) = origin else {
        return;
    };
    if config
        .allowed_origins
        .iter()
        .any(|allowed| allowed == "*" || allowed == origin)
    {
        if let Ok(value) = HeaderValue::from_str(origin) {
            headers.insert(header::ACCESS_CONTROL_ALLOW_ORIGIN, value);
        }
    }
    headers.insert(
        header::ACCESS_CONTROL_ALLOW_CREDENTIALS,
        HeaderValue::from_static("true"),
    );
    headers.insert(header::VARY, HeaderValue::from_static("Origin"));
}

fn cors_preflight(config: &GatewayConfig, request_headers: &HeaderMap) -> Response<Body> {
    let origin = request_headers
        .get(header::ORIGIN)
        .and_then(|value| value.to_str().ok());
    let allowed = origin.is_some_and(|origin| {
        config
            .allowed_origins
            .iter()
            .any(|candidate| candidate == "*" || candidate == origin)
    });
    if !allowed {
        return Response::builder()
            .status(StatusCode::BAD_REQUEST)
            .header(header::CONTENT_TYPE, "text/plain; charset=utf-8")
            .body(Body::from("Disallowed CORS origin"))
            .expect("CORS error response");
    }
    let mut response = Response::builder()
        .status(StatusCode::OK)
        .header(header::CONTENT_TYPE, "text/plain; charset=utf-8")
        .header(header::ACCESS_CONTROL_ALLOW_METHODS, "GET, POST, OPTIONS")
        .header(header::ACCESS_CONTROL_ALLOW_CREDENTIALS, "true")
        .header(header::ACCESS_CONTROL_MAX_AGE, "600")
        .header(header::VARY, "Origin")
        .body(Body::from("OK"))
        .expect("CORS preflight response");
    if let Some(requested_headers) = request_headers.get("access-control-request-headers") {
        response.headers_mut().insert(
            header::ACCESS_CONTROL_ALLOW_HEADERS,
            requested_headers.clone(),
        );
    }
    response
}

fn request_body_is_too_large(headers: &HeaderMap, limit: usize) -> bool {
    headers
        .get(header::CONTENT_LENGTH)
        .and_then(|value| value.to_str().ok())
        .and_then(|value| value.parse::<u64>().ok())
        .is_some_and(|length| length > limit as u64)
}

fn json_response(status: StatusCode, value: Value) -> Response<Body> {
    Response::builder()
        .status(status)
        .header(header::CONTENT_TYPE, "application/json")
        .body(Body::from(
            serde_json::to_vec(&value).expect("serialize gateway JSON response"),
        ))
        .expect("JSON response")
}

fn not_found() -> Response<Body> {
    json_response(StatusCode::NOT_FOUND, json!({"detail": "Not Found"}))
}

fn payload_too_large() -> Response<Body> {
    json_response(
        StatusCode::PAYLOAD_TOO_LARGE,
        json!({"detail": "Request body too large"}),
    )
}

fn bad_gateway(correlation_id: &str) -> Response<Body> {
    json_response(
        StatusCode::BAD_GATEWAY,
        json!({
            "detail": "Python worker unavailable",
            "request_id": correlation_id,
        }),
    )
}

fn gateway_timeout(correlation_id: &str) -> Response<Body> {
    json_response(
        StatusCode::GATEWAY_TIMEOUT,
        json!({
            "detail": "Python worker timeout",
            "request_id": correlation_id,
        }),
    )
}

/// Run a gateway instance without process supervision. Production uses the
/// `horo_server` binary, which owns the Uvicorn child lifecycle.
pub async fn run_rust_axum_server(port: u16) -> std::io::Result<()> {
    let app = build_gateway(GatewayConfig::new("http://127.0.0.1:8001".to_string()));
    let address = SocketAddr::from(([0, 0, 0, 0], port));
    println!("[INFO] Axum gateway listening on http://{address}");
    let listener = tokio::net::TcpListener::bind(address).await?;
    axum::serve(listener, app).await
}

/// Run native Rust Axum Web API Server on the specified port.
#[cfg(feature = "python")]
#[pyfunction]
pub fn start_rust_axum_server(port: u16) -> PyResult<()> {
    let runtime = tokio::runtime::Runtime::new()
        .map_err(|error| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(error.to_string()))?;
    runtime
        .block_on(run_rust_axum_server(port))
        .map_err(|error| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(error.to_string()))
}
