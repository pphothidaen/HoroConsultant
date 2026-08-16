/*!
 * rust_core/src/observability.rs
 * Wire-compatible Prometheus metrics collection for the Python fallback and
 * the pure Rust gateway.
 */

#[cfg(feature = "python")]
use pyo3::prelude::*;
use std::collections::BTreeMap;
use std::sync::Mutex;

use lazy_static::lazy_static;

#[derive(Debug, Default)]
pub struct MetricsRegistry {
    request_counts: BTreeMap<(String, String, u16), u64>,
    request_latency_sums: BTreeMap<(String, String), f64>,
    rag_count: u64,
    rag_latency_sum: f64,
    llm_counts: BTreeMap<(String, String), u64>,
    llm_latency_sums: BTreeMap<String, f64>,
}

impl MetricsRegistry {
    pub fn record_request(
        &mut self,
        method: &str,
        endpoint: &str,
        status_code: u16,
        duration_seconds: f64,
    ) -> u64 {
        *self
            .request_counts
            .entry((method.to_string(), endpoint.to_string(), status_code))
            .or_insert(0) += 1;
        *self
            .request_latency_sums
            .entry((method.to_string(), endpoint.to_string()))
            .or_insert(0.0) += duration_seconds;
        self.request_counts.values().sum()
    }

    pub fn record_rag_search(&mut self, duration_seconds: f64) -> u64 {
        self.rag_count += 1;
        self.rag_latency_sum += duration_seconds;
        self.rag_count
    }

    pub fn record_llm_inference(&mut self, provider: &str, status: &str, duration_seconds: f64) {
        *self
            .llm_counts
            .entry((provider.to_string(), status.to_string()))
            .or_insert(0) += 1;
        *self
            .llm_latency_sums
            .entry(provider.to_string())
            .or_insert(0.0) += duration_seconds;
    }

    pub fn generate_metrics_text(&self, uptime_seconds: f64) -> String {
        let mut lines = vec![
            "# HELP process_uptime_seconds Total application uptime in seconds".to_string(),
            "# TYPE process_uptime_seconds gauge".to_string(),
            format!("process_uptime_seconds {uptime_seconds:.2}"),
            String::new(),
            "# HELP http_requests_total Total count of HTTP requests".to_string(),
            "# TYPE http_requests_total counter".to_string(),
        ];
        for ((method, endpoint, status), count) in &self.request_counts {
            lines.push(format!(
                "http_requests_total{{method=\"{method}\",endpoint=\"{endpoint}\",status_code=\"{status}\"}} {count}"
            ));
        }
        lines.extend([
            String::new(),
            "# HELP http_request_duration_seconds_count Total number of HTTP request duration observations".to_string(),
            "# TYPE http_request_duration_seconds_count counter".to_string(),
        ]);
        let mut path_counts: BTreeMap<(&str, &str), u64> = BTreeMap::new();
        for ((method, endpoint, _), count) in &self.request_counts {
            *path_counts.entry((method, endpoint)).or_insert(0) += count;
        }
        for ((method, endpoint), count) in path_counts {
            lines.push(format!(
                "http_request_duration_seconds_count{{method=\"{method}\",endpoint=\"{endpoint}\"}} {count}"
            ));
        }
        lines.extend([
            String::new(),
            "# HELP http_request_duration_seconds_sum Total cumulative HTTP request duration"
                .to_string(),
            "# TYPE http_request_duration_seconds_sum counter".to_string(),
        ]);
        for ((method, endpoint), duration) in &self.request_latency_sums {
            lines.push(format!(
                "http_request_duration_seconds_sum{{method=\"{method}\",endpoint=\"{endpoint}\"}} {duration:.4}"
            ));
        }
        lines.extend([
            String::new(),
            "# HELP rag_search_total Total RAG vector store queries".to_string(),
            "# TYPE rag_search_total counter".to_string(),
            format!("rag_search_total {}", self.rag_count),
            String::new(),
            "# HELP rag_search_latency_seconds_sum Total RAG vector store retrieval duration"
                .to_string(),
            "# TYPE rag_search_latency_seconds_sum counter".to_string(),
            format!("rag_search_latency_seconds_sum {:.4}", self.rag_latency_sum),
        ]);
        for ((provider, status), count) in &self.llm_counts {
            lines.push(format!(
                "llm_inference_total{{provider=\"{provider}\",status=\"{status}\"}} {count}"
            ));
        }
        lines.join("\n") + "\n"
    }
}

lazy_static! {
    static ref GLOBAL_METRICS: Mutex<MetricsRegistry> = Mutex::new(MetricsRegistry::default());
}

/// Record an HTTP request. The PyO3 boundary accepts milliseconds for backward
/// compatibility and normalizes to the Python manager's seconds schema.
#[cfg(feature = "python")]
#[pyfunction]
pub fn record_http_metric_rust(
    method: &str,
    endpoint: &str,
    status_code: u16,
    latency_ms: f64,
) -> PyResult<u64> {
    let mut metrics = GLOBAL_METRICS
        .lock()
        .map_err(|_| pyo3::exceptions::PyRuntimeError::new_err("metrics lock poisoned"))?;
    Ok(metrics.record_request(method, endpoint, status_code, latency_ms / 1000.0))
}

#[cfg(feature = "python")]
#[pyfunction]
pub fn record_rag_metric_rust(latency_ms: f64) -> PyResult<u64> {
    let mut metrics = GLOBAL_METRICS
        .lock()
        .map_err(|_| pyo3::exceptions::PyRuntimeError::new_err("metrics lock poisoned"))?;
    Ok(metrics.record_rag_search(latency_ms / 1000.0))
}

#[cfg(feature = "python")]
#[pyfunction]
pub fn generate_prometheus_metrics_rust(uptime_seconds: f64) -> PyResult<String> {
    let metrics = GLOBAL_METRICS
        .lock()
        .map_err(|_| pyo3::exceptions::PyRuntimeError::new_err("metrics lock poisoned"))?;
    Ok(metrics.generate_metrics_text(uptime_seconds))
}
