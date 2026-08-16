/*!
 * rust_core/src/bin/horo_server.rs
 * PID-1 production entrypoint for the Axum gateway and private Uvicorn worker.
 */

use axum::Router;
use rust_core::server::{build_gateway, GatewayConfig};
use std::{
    future::{Future, IntoFuture},
    io,
    net::SocketAddr,
    process::Stdio,
    time::Duration,
};
use tokio::{
    net::TcpListener,
    process::{Child, Command},
    sync::oneshot,
    time::Instant,
};

const PUBLIC_ADDRESS: SocketAddr =
    SocketAddr::new(std::net::IpAddr::V4(std::net::Ipv4Addr::UNSPECIFIED), 8000);
const PYTHON_ORIGIN: &str = "http://127.0.0.1:8001";
const WORKER_SHUTDOWN_GRACE: Duration = Duration::from_secs(10);

fn python_worker_command(executable: &str) -> Command {
    let mut command = Command::new(executable);
    command
        .args([
            "-m",
            "uvicorn",
            "project.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8001",
            "--workers",
            "1",
        ])
        .stdin(Stdio::null())
        .env("AUTO_SYNC_ON_STARTUP", "false")
        .env("AUTO_SYNC_ENABLED", "false")
        .kill_on_drop(true);
    command
}

async fn wait_for_worker_ready(
    client: &reqwest::Client,
    python_origin: &str,
    timeout: Duration,
    retry_interval: Duration,
) -> Result<(), String> {
    let deadline = Instant::now() + timeout;
    let readiness_url = format!("{}/openapi.json", python_origin.trim_end_matches('/'));
    loop {
        if let Ok(response) = client.get(&readiness_url).send().await {
            if response.status().is_success() {
                return Ok(());
            }
        }
        if Instant::now() >= deadline {
            return Err(format!(
                "Python worker did not become ready within {} seconds",
                timeout.as_secs()
            ));
        }
        tokio::time::sleep(retry_interval).await;
    }
}

#[cfg(unix)]
fn forward_signal(pid: u32, signal: i32) -> io::Result<()> {
    unsafe extern "C" {
        fn kill(pid: i32, signal: i32) -> i32;
    }
    let result = unsafe { kill(pid as i32, signal) };
    if result == 0 {
        Ok(())
    } else {
        Err(io::Error::last_os_error())
    }
}

#[cfg(not(unix))]
fn forward_signal(_pid: u32, _signal: i32) -> io::Result<()> {
    Err(io::Error::new(
        io::ErrorKind::Unsupported,
        "signal forwarding is unavailable on this platform",
    ))
}

async fn terminate_child(child: &mut Child, signal: i32) {
    if child.try_wait().ok().flatten().is_some() {
        return;
    }
    #[cfg(unix)]
    if let Some(pid) = child.id() {
        let _ = forward_signal(pid, signal);
    }
    #[cfg(not(unix))]
    {
        let _ = child.start_kill();
    }
    if tokio::time::timeout(WORKER_SHUTDOWN_GRACE, child.wait())
        .await
        .is_err()
    {
        let _ = child.kill().await;
        let _ = child.wait().await;
    }
}

async fn supervise<F>(
    mut child: Child,
    listener: TcpListener,
    app: Router,
    signal: F,
) -> Result<(), String>
where
    F: Future<Output = i32>,
{
    let (shutdown_tx, shutdown_rx) = oneshot::channel::<()>();
    let mut shutdown_tx = Some(shutdown_tx);
    let server = axum::serve(listener, app)
        .with_graceful_shutdown(async move {
            let _ = shutdown_rx.await;
        })
        .into_future();
    tokio::pin!(server);
    tokio::pin!(signal);

    tokio::select! {
        child_result = child.wait() => {
            match child_result {
                Ok(status) => Err(format!("Python worker exited unexpectedly with status {status}")),
                Err(error) => Err(format!("failed waiting for Python worker: {error}")),
            }
        }
        signal_number = &mut signal => {
            if let Some(sender) = shutdown_tx.take() {
                let _ = sender.send(());
            }
            terminate_child(&mut child, signal_number).await;
            server
                .as_mut()
                .await
                .map_err(|error| format!("Axum gateway shutdown failed: {error}"))
        }
        server_result = &mut server => {
            terminate_child(&mut child, 15).await;
            match server_result {
                Ok(()) => Err("Axum gateway exited unexpectedly".to_string()),
                Err(error) => Err(format!("Axum gateway failed: {error}")),
            }
        }
    }
}

#[cfg(unix)]
async fn shutdown_signal() -> i32 {
    let mut terminate = tokio::signal::unix::signal(tokio::signal::unix::SignalKind::terminate())
        .expect("install SIGTERM handler");
    tokio::select! {
        result = tokio::signal::ctrl_c() => {
            if result.is_err() {
                15
            } else {
                2
            }
        }
        _ = terminate.recv() => 15,
    }
}

#[cfg(not(unix))]
async fn shutdown_signal() -> i32 {
    let _ = tokio::signal::ctrl_c().await;
    2
}

fn duration_from_env(name: &str, default_seconds: u64) -> Duration {
    std::env::var(name)
        .ok()
        .and_then(|value| value.parse::<u64>().ok())
        .map(Duration::from_secs)
        .unwrap_or_else(|| Duration::from_secs(default_seconds))
}

fn usize_from_env(name: &str, default: usize) -> usize {
    std::env::var(name)
        .ok()
        .and_then(|value| value.parse::<usize>().ok())
        .filter(|value| *value > 0)
        .unwrap_or(default)
}

async fn run() -> Result<(), String> {
    let python_executable =
        std::env::var("PYTHON_EXECUTABLE").unwrap_or_else(|_| "python3".to_string());
    let mut child = python_worker_command(&python_executable)
        .spawn()
        .map_err(|error| format!("failed to start Python worker directly: {error}"))?;

    let startup_timeout = duration_from_env("PYTHON_WORKER_STARTUP_TIMEOUT_SECONDS", 60);
    let readiness_client = reqwest::Client::builder()
        .timeout(Duration::from_secs(2))
        .build()
        .map_err(|error| format!("failed to build readiness client: {error}"))?;
    let readiness = wait_for_worker_ready(
        &readiness_client,
        PYTHON_ORIGIN,
        startup_timeout,
        Duration::from_millis(200),
    );
    tokio::pin!(readiness);
    tokio::select! {
        status = child.wait() => {
            return match status {
                Ok(status) => Err(format!("Python worker exited before readiness with status {status}")),
                Err(error) => Err(format!("failed waiting for Python worker readiness: {error}")),
            };
        }
        result = &mut readiness => {
            if let Err(error) = result {
                terminate_child(&mut child, 15).await;
                return Err(error);
            }
        }
    }

    let listener = match TcpListener::bind(PUBLIC_ADDRESS).await {
        Ok(listener) => listener,
        Err(error) => {
            terminate_child(&mut child, 15).await;
            return Err(format!(
                "failed to bind Axum gateway on {PUBLIC_ADDRESS}: {error}"
            ));
        }
    };
    let proxy_timeout = duration_from_env("GATEWAY_PROXY_TIMEOUT_SECONDS", 30);
    let max_body_bytes = usize_from_env("GATEWAY_MAX_BODY_BYTES", 2 * 1024 * 1024);
    let config = GatewayConfig::new(PYTHON_ORIGIN.to_string())
        .with_proxy_timeout(proxy_timeout)
        .with_max_body_bytes(max_body_bytes);
    let app = build_gateway(config);

    println!("[OK] Python worker ready on {PYTHON_ORIGIN}");
    println!("[INFO] Axum gateway listening on http://{PUBLIC_ADDRESS}");
    supervise(child, listener, app, shutdown_signal()).await
}

#[tokio::main]
async fn main() {
    if let Err(error) = run().await {
        eprintln!("[ERROR] HoroConsultant gateway stopped: {error}");
        std::process::exit(1);
    }
}

#[cfg(test)]
mod supervisor_tests {
    use super::*;
    use axum::{http::StatusCode, routing::get, Router};
    use std::{
        future,
        process::Stdio,
        sync::{
            atomic::{AtomicUsize, Ordering},
            Arc,
        },
        time::Duration,
    };
    use tokio::io::{AsyncBufReadExt, BufReader};

    #[test]
    fn python_worker_command_invokes_uvicorn_directly_on_loopback() {
        let command = python_worker_command("python3");
        let command = command.as_std();
        let arguments = command
            .get_args()
            .map(|argument| argument.to_string_lossy().into_owned())
            .collect::<Vec<_>>();

        assert_eq!(command.get_program(), "python3");
        assert_eq!(
            arguments,
            [
                "-m",
                "uvicorn",
                "project.main:app",
                "--host",
                "127.0.0.1",
                "--port",
                "8001",
                "--workers",
                "1",
            ]
        );
        let environment = command
            .get_envs()
            .filter_map(|(name, value)| value.map(|value| (name, value)))
            .collect::<std::collections::HashMap<_, _>>();
        assert_eq!(
            environment.get(std::ffi::OsStr::new("AUTO_SYNC_ON_STARTUP")),
            Some(&std::ffi::OsStr::new("false"))
        );
        assert_eq!(
            environment.get(std::ffi::OsStr::new("AUTO_SYNC_ENABLED")),
            Some(&std::ffi::OsStr::new("false"))
        );
    }

    #[tokio::test]
    async fn readiness_wait_retries_until_the_worker_serves_openapi() {
        let attempts = Arc::new(AtomicUsize::new(0));
        let handler_attempts = attempts.clone();
        let app = Router::new().route(
            "/openapi.json",
            get(move || {
                let attempt = handler_attempts.fetch_add(1, Ordering::Relaxed);
                async move {
                    if attempt < 2 {
                        StatusCode::SERVICE_UNAVAILABLE
                    } else {
                        StatusCode::OK
                    }
                }
            }),
        );
        let listener = tokio::net::TcpListener::bind("127.0.0.1:0").await.unwrap();
        let address = listener.local_addr().unwrap();
        let server = tokio::spawn(async move { axum::serve(listener, app).await.unwrap() });

        wait_for_worker_ready(
            &reqwest::Client::new(),
            &format!("http://{address}"),
            Duration::from_secs(2),
            Duration::from_millis(5),
        )
        .await
        .expect("worker becomes ready");

        assert!(attempts.load(Ordering::Relaxed) >= 3);
        server.abort();
    }

    #[tokio::test]
    async fn supervisor_fails_fast_when_the_python_worker_exits() {
        let child = tokio::process::Command::new("/usr/bin/false")
            .spawn()
            .expect("spawn failing child");
        let listener = tokio::net::TcpListener::bind("127.0.0.1:0").await.unwrap();
        let app = Router::new().route("/health", get(|| async { "ok" }));

        let error = supervise(child, listener, app, future::pending::<i32>())
            .await
            .expect_err("worker failure must stop the gateway");

        assert!(error.contains("Python worker exited"), "{error}");
    }

    #[tokio::test]
    async fn worker_failure_does_not_wait_for_in_flight_gateway_requests() {
        let child = tokio::process::Command::new("python3")
            .args(["-c", "import time; time.sleep(0.2)"])
            .spawn()
            .expect("spawn delayed failing child");
        let listener = tokio::net::TcpListener::bind("127.0.0.1:0").await.unwrap();
        let address = listener.local_addr().unwrap();
        let request_started = Arc::new(tokio::sync::Notify::new());
        let handler_started = request_started.clone();
        let app = Router::new().route(
            "/hang",
            get(move || {
                let handler_started = handler_started.clone();
                async move {
                    handler_started.notify_one();
                    tokio::time::sleep(Duration::from_secs(30)).await;
                    "late"
                }
            }),
        );
        let supervisor = tokio::spawn(supervise(child, listener, app, future::pending::<i32>()));
        let request = tokio::spawn(async move {
            let _ = reqwest::get(format!("http://{address}/hang")).await;
        });
        tokio::time::timeout(Duration::from_secs(1), request_started.notified())
            .await
            .expect("request reaches gateway");

        let result = tokio::time::timeout(Duration::from_millis(500), supervisor)
            .await
            .expect("worker failure stops gateway immediately")
            .expect("supervisor task joins")
            .expect_err("worker failure is reported");

        assert!(result.contains("Python worker exited"), "{result}");
        request.abort();
    }

    #[cfg(unix)]
    #[tokio::test]
    async fn termination_signal_is_forwarded_to_the_worker_process() {
        let mut child = tokio::process::Command::new("python3")
            .args([
                "-c",
                "import signal,sys,time; signal.signal(signal.SIGTERM, lambda *_: sys.exit(42)); print('ready', flush=True); time.sleep(30)",
            ])
            .stdout(Stdio::piped())
            .spawn()
            .expect("spawn signal-aware child");
        let mut ready = String::new();
        BufReader::new(child.stdout.take().expect("child stdout"))
            .read_line(&mut ready)
            .await
            .expect("read child readiness");
        assert_eq!(ready.trim(), "ready");

        forward_signal(child.id().expect("child PID"), 15).expect("forward SIGTERM");
        let status = tokio::time::timeout(Duration::from_secs(2), child.wait())
            .await
            .expect("child exits after signal")
            .expect("wait for child");

        assert_eq!(status.code(), Some(42));
    }
}
