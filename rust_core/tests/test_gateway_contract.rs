use axum::{
    body::{to_bytes, Body},
    extract::State,
    http::{header, Request, Response, StatusCode},
    routing::any,
    Router,
};
use reqwest::{Client, Method};
use rust_core::server::{build_gateway, GatewayConfig};
use serde_json::{json, Value};
use std::{
    sync::{
        atomic::{AtomicUsize, Ordering},
        Arc,
    },
    time::Duration,
};
use tokio::task::JoinHandle;

const OPENAPI_GOLDEN: &str = include_str!("../../project/tests/goldens/openapi.json");
const BAZI_GOLDEN: &str = include_str!("../../project/tests/goldens/bazi_response.json");

struct RunningServer {
    base_url: String,
    task: JoinHandle<()>,
}

impl Drop for RunningServer {
    fn drop(&mut self) {
        self.task.abort();
    }
}

async fn start_server(app: Router) -> RunningServer {
    let listener = tokio::net::TcpListener::bind("127.0.0.1:0")
        .await
        .expect("bind test server");
    let address = listener.local_addr().expect("test server address");
    let task = tokio::spawn(async move {
        axum::serve(listener, app).await.expect("serve test router");
    });
    RunningServer {
        base_url: format!("http://{address}"),
        task,
    }
}

async fn upstream_handler(
    State(request_count): State<Arc<AtomicUsize>>,
    request: Request<Body>,
) -> Response<Body> {
    request_count.fetch_add(1, Ordering::Relaxed);
    let method = request.method().clone();
    let uri = request.uri().clone();
    let headers = request.headers().clone();
    let body = to_bytes(request.into_body(), 8 * 1024 * 1024)
        .await
        .expect("read upstream request");

    if uri.path() == "/openapi.json" {
        return Response::builder()
            .status(StatusCode::OK)
            .header(header::CONTENT_TYPE, "application/json")
            .body(Body::from(OPENAPI_GOLDEN.as_bytes()))
            .expect("OpenAPI response");
    }
    if uri.path() == "/_internal/v1/bazi/render" {
        let golden: Value = serde_json::from_str(BAZI_GOLDEN).expect("BaZi golden JSON");
        let response = json!({
            "svg_content": golden["svg_content"],
            "zodiac_svg": golden["zodiac_svg"],
        });
        return Response::builder()
            .status(StatusCode::OK)
            .header(header::CONTENT_TYPE, "application/json")
            .body(Body::from(
                serde_json::to_vec(&response).expect("renderer response"),
            ))
            .expect("renderer response");
    }
    if uri.path() == "/api/v1/bazi/calculate" {
        return Response::builder()
            .status(StatusCode::UNPROCESSABLE_ENTITY)
            .header(header::CONTENT_TYPE, "application/json")
            .body(Body::from(r#"{"detail":"python validation"}"#))
            .expect("validation response");
    }
    if uri.path() == "/admin/catalog" && uri.query() == Some("timeout=1") {
        tokio::time::sleep(Duration::from_millis(100)).await;
    }
    if uri.path() == "/admin/grayzone/answer" {
        return Response::builder()
            .status(StatusCode::MULTI_STATUS)
            .header(header::CONTENT_TYPE, "application/vnd.horo+json")
            .header("x-seen-method", method.as_str())
            .header("x-seen-uri", uri.to_string())
            .header(
                "x-seen-authorization",
                headers
                    .get(header::AUTHORIZATION)
                    .and_then(|value| value.to_str().ok())
                    .unwrap_or_default(),
            )
            .header(
                "x-request-id",
                headers
                    .get("x-request-id")
                    .and_then(|value| value.to_str().ok())
                    .unwrap_or_default(),
            )
            .header(header::CONNECTION, "x-remove-me")
            .header("x-remove-me", "hop-by-hop")
            .body(Body::from(body))
            .expect("echo response");
    }

    Response::builder()
        .status(StatusCode::NO_CONTENT)
        .body(Body::empty())
        .expect("default upstream response")
}

async fn gateway_pair(
    configure: impl FnOnce(GatewayConfig) -> GatewayConfig,
) -> (RunningServer, RunningServer, Arc<AtomicUsize>) {
    let request_count = Arc::new(AtomicUsize::new(0));
    let upstream = start_server(
        Router::new()
            .fallback(any(upstream_handler))
            .with_state(request_count.clone()),
    )
    .await;
    let config = configure(GatewayConfig::new(upstream.base_url.clone()));
    let gateway = start_server(build_gateway(config)).await;
    (upstream, gateway, request_count)
}

#[tokio::test]
async fn all_42_openapi_paths_and_44_operations_remain_reachable() {
    let (_upstream, gateway, _count) = gateway_pair(|config| config).await;
    let client = Client::new();
    let routes = [
        ("POST", "/admin/auth/google"),
        ("GET", "/admin/auth/config"),
        ("GET", "/admin/catalog"),
        ("GET", "/admin/catalog/summary"),
        ("GET", "/admin/catalog/source/source-1"),
        ("GET", "/admin/grayzone"),
        ("POST", "/admin/grayzone/answer"),
        ("DELETE", "/admin/grayzone/answer"),
        ("GET", "/admin/finetune/status"),
        ("POST", "/admin/finetune/export-grayzone"),
        ("POST", "/admin/finetune/merge"),
        ("POST", "/admin/finetune/trigger"),
        ("GET", "/admin/finetune/download"),
        ("GET", "/admin/finetune/download-grayzone"),
        ("GET", "/admin/code-review"),
        ("GET", "/hitl/queue"),
        ("GET", "/hitl/item/item-1"),
        ("POST", "/hitl/draft/item-1"),
        ("POST", "/hitl/review/item-1"),
        ("DELETE", "/hitl/review/item-1"),
        ("GET", "/hitl/stats"),
        ("GET", "/hitl/export"),
        ("POST", "/hitl/batch-draft"),
        ("POST", "/api/v1/bazi/calculate"),
        ("GET", "/api/v1/ziwei/calculate"),
        ("GET", "/api/v1/qimen/calculate"),
        ("GET", "/api/v1/liuren/calculate"),
        ("GET", "/api/v1/iching/calculate"),
        ("GET", "/api/v1/xuankong/calculate"),
        ("GET", "/api/v1/zeji/calculate"),
        ("GET", "/api/v1/thaivedic/calculate"),
        ("GET", "/api/v1/western/calculate"),
        ("GET", "/api/v1/numerology/calculate"),
        ("GET", "/api/v1/eot?date=2026-08-03"),
        ("POST", "/api/v1/location/resolve"),
        ("POST", "/bazi/interpret"),
        ("POST", "/v1/bazi/interpret"),
        ("POST", "/api/v1/bazi/interpret"),
        ("POST", "/api/v1/bazi/validate"),
        ("GET", "/"),
        ("GET", "/admin"),
        ("GET", "/hitl-studio"),
        ("GET", "/api/v1/health"),
        ("GET", "/health"),
    ];
    let distinct_paths = routes
        .iter()
        .map(|(_, path)| path.split('?').next().expect("path"))
        .collect::<std::collections::HashSet<_>>();
    assert_eq!(routes.len(), 44);
    assert_eq!(distinct_paths.len(), 42);

    for (method, path) in routes {
        let mut request = client.request(
            Method::from_bytes(method.as_bytes()).expect("HTTP method"),
            format!("{}{path}", gateway.base_url),
        );
        if method == "POST" {
            let body = if path == "/api/v1/bazi/calculate" {
                json!({
                    "birth_datetime": "1990-05-15 14:30:00",
                    "longitude": 100.493,
                    "utc_offset_hours": 7.0,
                    "unknown_hour": false,
                })
            } else {
                json!({})
            };
            request = request.json(&body);
        }
        let response = request.send().await.expect("gateway route response");
        assert_ne!(response.status(), StatusCode::NOT_FOUND, "{method} {path}");
        assert_ne!(
            response.status(),
            StatusCode::METHOD_NOT_ALLOWED,
            "{method} {path}"
        );
    }
}

#[tokio::test]
async fn proxy_preserves_method_query_body_status_content_type_headers_and_correlation_id() {
    let (_upstream, gateway, _count) = gateway_pair(|config| config).await;
    let payload = b"\x00raw-request-bytes\xff".to_vec();
    let response = Client::new()
        .post(format!(
            "{}/admin/grayzone/answer?draft=1",
            gateway.base_url
        ))
        .header(header::AUTHORIZATION, "Bearer test-value")
        .header("x-request-id", "request-123")
        .body(payload.clone())
        .send()
        .await
        .expect("proxy response");

    assert_eq!(response.status(), StatusCode::MULTI_STATUS);
    assert_eq!(
        response.headers().get(header::CONTENT_TYPE).unwrap(),
        "application/vnd.horo+json"
    );
    assert_eq!(response.headers().get("x-seen-method").unwrap(), "POST");
    assert_eq!(
        response.headers().get("x-seen-uri").unwrap(),
        "/admin/grayzone/answer?draft=1"
    );
    assert_eq!(
        response.headers().get("x-seen-authorization").unwrap(),
        "Bearer test-value"
    );
    assert_eq!(
        response.headers().get("x-request-id").unwrap(),
        "request-123"
    );
    assert!(response.headers().get(header::CONNECTION).is_none());
    assert!(response.headers().get("x-remove-me").is_none());
    assert_eq!(response.bytes().await.expect("proxy body"), payload);
}

#[tokio::test]
async fn openapi_and_python_response_bytes_are_forwarded_without_reencoding() {
    let (_upstream, gateway, _count) = gateway_pair(|config| config).await;
    let response = Client::new()
        .get(format!("{}/openapi.json", gateway.base_url))
        .send()
        .await
        .expect("OpenAPI proxy response");

    assert_eq!(response.status(), StatusCode::OK);
    assert_eq!(
        response.headers().get(header::CONTENT_TYPE).unwrap(),
        "application/json"
    );
    assert_eq!(
        response.bytes().await.expect("OpenAPI bytes"),
        OPENAPI_GOLDEN.as_bytes()
    );
}

#[tokio::test]
async fn non_schema_ui_docs_metrics_and_health_aliases_preserve_their_methods() {
    let (_upstream, gateway, _count) = gateway_pair(|config| config).await;
    let client = Client::new();
    let routes = [
        ("GET", "/app.js"),
        ("GET", "/style.css"),
        ("GET", "/static/test-asset.png"),
        ("GET", "/docs"),
        ("HEAD", "/docs"),
        ("GET", "/docs/oauth2-redirect"),
        ("GET", "/redoc"),
        ("GET", "/openapi.json"),
        ("HEAD", "/openapi.json"),
        ("GET", "/metrics"),
        ("GET", "/metrics/seed-dummy"),
        ("POST", "/metrics/seed-dummy"),
        ("GET", "/api/health"),
    ];

    for (method, path) in routes {
        let response = client
            .request(
                Method::from_bytes(method.as_bytes()).unwrap(),
                format!("{}{path}", gateway.base_url),
            )
            .send()
            .await
            .expect("non-schema route response");
        assert_ne!(response.status(), StatusCode::NOT_FOUND, "{method} {path}");
        assert_ne!(
            response.status(),
            StatusCode::METHOD_NOT_ALLOWED,
            "{method} {path}"
        );
    }
}

#[tokio::test]
async fn native_health_exposes_liveness_and_secret_free_runtime_identity() {
    let (_upstream, gateway, _count) = gateway_pair(|config| config).await;
    let client = Client::new();

    let liveness: Value = client
        .get(format!("{}/health", gateway.base_url))
        .send()
        .await
        .expect("liveness response")
        .json()
        .await
        .expect("liveness JSON");
    assert_eq!(liveness["status"], "ok");
    assert_eq!(liveness["service"], "Computational Metaphysics Engine");

    let readiness: Value = client
        .get(format!("{}/api/v1/health", gateway.base_url))
        .send()
        .await
        .expect("readiness response")
        .json()
        .await
        .expect("readiness JSON");
    assert_eq!(readiness["status"], "ok");
    assert_eq!(readiness["gateway"], "rust_axum");
    assert_eq!(readiness["python_worker"], "ready");
    assert_eq!(readiness["runtime_backend"]["rust_available"], true);
    assert!(readiness["runtime_backend"]["active_kernels"]
        .as_array()
        .unwrap()
        .iter()
        .any(|kernel| kernel == "calculate_bazi"));
    let serialized = serde_json::to_string(&readiness).unwrap().to_lowercase();
    assert!(!serialized.contains("token"));
    assert!(!serialized.contains("secret"));
}

#[tokio::test]
async fn native_equation_of_time_preserves_success_and_validation_contracts() {
    let (_upstream, gateway, _count) = gateway_pair(|config| config).await;
    let client = Client::new();

    let valid = client
        .get(format!("{}/api/v1/eot?date=2026-08-03", gateway.base_url))
        .send()
        .await
        .expect("equation-of-time response");
    assert_eq!(valid.status(), StatusCode::OK);
    assert_eq!(
        valid.json::<Value>().await.unwrap(),
        json!({"date": "2026-08-03", "eot_minutes": -6.3976})
    );

    let invalid = client
        .get(format!("{}/api/v1/eot?date=not-a-date", gateway.base_url))
        .send()
        .await
        .expect("invalid equation-of-time response");
    assert_eq!(invalid.status(), StatusCode::UNPROCESSABLE_ENTITY);
    assert_eq!(
        invalid.json::<Value>().await.unwrap(),
        json!({"detail": "Invalid date format, use YYYY-MM-DD"})
    );
}

#[tokio::test]
async fn native_bazi_matches_the_literal_python_chart_contract() {
    let (_upstream, gateway, _count) = gateway_pair(|config| config).await;
    let response = Client::new()
        .post(format!("{}/api/v1/bazi/calculate", gateway.base_url))
        .json(&json!({
            "birth_datetime": "1990-05-15 14:30:00",
            "longitude": 100.493,
            "utc_offset_hours": 7.0,
            "unknown_hour": false,
        }))
        .send()
        .await
        .expect("native BaZi response");
    assert_eq!(response.status(), StatusCode::OK);
    let mut actual: Value = response.json().await.expect("BaZi response JSON");
    actual["calculation_timestamp"] = Value::String("<timestamp>".to_string());
    let golden: Value = serde_json::from_str(BAZI_GOLDEN).expect("BaZi golden JSON");

    assert_eq!(actual, golden);
}

#[tokio::test]
async fn unknown_targets_fail_closed_without_contacting_python() {
    let (_upstream, gateway, request_count) = gateway_pair(|config| config).await;
    let response = Client::new()
        .post(format!("{}/api/v1/proxy/admin/catalog", gateway.base_url))
        .body("must-not-leave-gateway")
        .send()
        .await
        .expect("closed proxy response");

    assert_eq!(response.status(), StatusCode::NOT_FOUND);
    assert_eq!(request_count.load(Ordering::Relaxed), 0);
}

#[tokio::test]
async fn payload_limit_timeout_and_cors_are_enforced_at_the_gateway_boundary() {
    let (_upstream, gateway, _count) = gateway_pair(|config| {
        config
            .with_max_body_bytes(16)
            .with_proxy_timeout(Duration::from_millis(10))
            .with_allowed_origins(vec!["*".to_string()])
    })
    .await;
    let client = Client::new();

    let oversized = client
        .post(format!("{}/admin/grayzone/answer", gateway.base_url))
        .body(vec![b'x'; 17])
        .send()
        .await
        .expect("payload-limit response");
    assert_eq!(oversized.status(), StatusCode::PAYLOAD_TOO_LARGE);

    let timed_out = client
        .get(format!("{}/admin/catalog?timeout=1", gateway.base_url))
        .header("x-request-id", "timeout-123")
        .send()
        .await
        .expect("timeout response");
    assert_eq!(timed_out.status(), StatusCode::GATEWAY_TIMEOUT);
    assert_eq!(
        timed_out.headers().get("x-request-id").unwrap(),
        "timeout-123"
    );

    let preflight = client
        .request(
            Method::OPTIONS,
            format!("{}/api/v1/bazi/calculate", gateway.base_url),
        )
        .header(header::ORIGIN, "https://frontend.example")
        .header("access-control-request-method", "POST")
        .header(
            "access-control-request-headers",
            "content-type,x-request-id",
        )
        .send()
        .await
        .expect("CORS preflight response");
    assert_eq!(preflight.status(), StatusCode::OK);
    assert_eq!(preflight.text().await.expect("preflight body"), "OK");
}

#[tokio::test]
async fn malformed_json_fuzz_never_panics_or_enters_the_native_calculator() {
    let (_upstream, gateway, _count) = gateway_pair(|config| config).await;
    let client = Client::new();

    for seed in 0_u16..512 {
        let malformed = format!(
            r#"{{"seed":{seed},"unterminated":"{}""#,
            "x".repeat((seed % 31) as usize)
        );
        let response = client
            .post(format!("{}/api/v1/bazi/calculate", gateway.base_url))
            .header(header::CONTENT_TYPE, "application/json")
            .body(malformed)
            .send()
            .await
            .expect("malformed request response");
        assert_eq!(
            response.status(),
            StatusCode::UNPROCESSABLE_ENTITY,
            "seed {seed}"
        );
    }
}
