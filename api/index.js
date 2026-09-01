// api/index.js -- Least-privilege Vercel gateway for the canonical HF backend.

import { applyCorsPolicy } from "./gateway.js";

const CANONICAL_HF_BACKEND_ORIGIN =
  "https://pphothidaen-horoconsultant-core-backend.hf.space";
const DEFAULT_BACKEND_TIMEOUT_MS = 8_000;
const MAX_BACKEND_TIMEOUT_MS = 30_000;
const MAX_REQUEST_BODY_BYTES = 2 * 1024 * 1024;
const PUBLIC_API_PATH = /^\/api\/v[123](?:\/[A-Za-z0-9._~!$&'()*+,;=:@/-]*)?$/;
const PUBLIC_READ_PATHS = new Set(["/health", "/docs", "/openapi.json"]);
const PUBLIC_MUTATION_PATHS = new Set([
  "/api/v1/location/resolve",
  "/api/v1/bazi/calculate",
  "/api/v1/bazi/interpret",
  "/api/v1/simulation/simulate-scenarios",
  "/api/v1/synastry/analyze",
  "/api/v1/luopan/calculate",
  "/api/v1/dream/interpret",
  "/api/v2/calculate/unified",
  "/api/v2/mian_xiang/analyze",
  "/api/v2/chat/prompt-pills",
  "/api/v2/chat/stream",
  "/api/v2/chat/consult",
  "/api/v3/calculate",
]);
const ADMIN_STARTUP_ROUTE_METHODS = new Map([
  ["/admin/auth/config", ["GET"]],
  ["/admin/auth/google", ["POST"]],
  ["/admin/catalog/summary", ["GET"]],
  ["/admin/grayzone", ["GET"]],
  ["/admin/finetune/status", ["GET"]],
  ["/admin/provider-pools", ["GET"]],
  ["/hitl/stats", ["GET"]],
]);
const PRIVILEGED_PATH_SEGMENT = /(?:^|\/)(?:admin|hitl)(?:\/|$)/i;

/**
 * Resolve the sole authorized Docker backend. Environment configuration may
 * select only the canonical HF Space origin; missing or different targets fail
 * closed rather than falling through to another provider or local template.
 */
export function configuredBackendOrigin(environment = process.env) {
  const configured = typeof environment?.HF_BACKEND_URL === "string"
    ? environment.HF_BACKEND_URL.trim()
    : "";
  if (!configured) return null;

  try {
    const parsed = new URL(configured);
    if (parsed.protocol !== "https:"
      || parsed.username
      || parsed.password
      || parsed.pathname !== "/"
      || parsed.search
      || parsed.hash
      || parsed.origin !== CANONICAL_HF_BACKEND_ORIGIN) {
      return null;
    }
    return parsed.origin;
  } catch {
    return null;
  }
}

function configuredBackendTimeoutMs(environment = process.env) {
  const parsed = Number.parseInt(environment?.VERCEL_BACKEND_TIMEOUT_MS || "", 10);
  if (!Number.isFinite(parsed) || parsed <= 0) return DEFAULT_BACKEND_TIMEOUT_MS;
  return Math.min(parsed, MAX_BACKEND_TIMEOUT_MS);
}

const BACKEND_ORIGIN = configuredBackendOrigin(process.env);
const BACKEND_TIMEOUT_MS = configuredBackendTimeoutMs(process.env);

function requestPath(request) {
  let requestUrl;
  try {
    requestUrl = new URL(request.url || "/", "https://gateway.invalid");
  } catch {
    return null;
  }

  const rawPath = requestUrl.searchParams.get("path");
  if (typeof rawPath !== "string"
    || !rawPath.startsWith("/")
    || rawPath.length > 2048
    || rawPath.includes("%")
    || rawPath.includes("\\")
    || rawPath.includes("//")
    || rawPath.includes("?")
    || rawPath.includes("#")
    || /[\u0000-\u001F\u007F]/.test(rawPath)) {
    return null;
  }

  const segments = rawPath.split("/");
  if (segments.some(segment => segment === "." || segment === "..")) return null;
  if (PRIVILEGED_PATH_SEGMENT.test(rawPath)
    && !ADMIN_STARTUP_ROUTE_METHODS.has(rawPath)) return null;
  if (!PUBLIC_READ_PATHS.has(rawPath)
    && !PUBLIC_API_PATH.test(rawPath)
    && !ADMIN_STARTUP_ROUTE_METHODS.has(rawPath)) return null;

  const query = new URLSearchParams();
  for (const [key, value] of requestUrl.searchParams.entries()) {
    if (key !== "path") query.append(key, value);
  }
  return `${rawPath}${query.size ? `?${query.toString()}` : ""}`;
}

function allowedMethods(path) {
  const pathname = path.split("?", 1)[0];
  if (ADMIN_STARTUP_ROUTE_METHODS.has(pathname)) return ADMIN_STARTUP_ROUTE_METHODS.get(pathname);
  if (PUBLIC_READ_PATHS.has(pathname)) return ["GET"];
  if (PUBLIC_MUTATION_PATHS.has(pathname)) return ["POST"];
  if (PUBLIC_API_PATH.test(pathname)) return ["GET"];
  return [];
}

function adminTokenRequired(path) {
  const pathname = path.split("?", 1)[0];
  return ADMIN_STARTUP_ROUTE_METHODS.has(pathname)
    && pathname !== "/admin/auth/config"
    && pathname !== "/admin/auth/google";
}

function hasBearerToken(request) {
  return /^Bearer\s+[^\s]{20,}$/.test(readHeader(request.headers, "authorization"));
}

function methodAllowed(method, path) {
  return allowedMethods(path).includes(String(method || "GET").toUpperCase());
}

function readHeader(headers = {}, name) {
  const expected = name.toLowerCase();
  const entry = Object.entries(headers).find(([key]) => key.toLowerCase() === expected);
  if (!entry || Array.isArray(entry[1])) return "";
  return typeof entry[1] === "string" ? entry[1] : String(entry[1]);
}

function safeCorrelationIdFor(request, upstreamId = "") {
  const candidate = upstreamId || readHeader(request.headers, "x-request-id");
  if (/^[A-Za-z0-9._:-]{1,128}$/.test(candidate)
    && !/\b(?:\d{1,3}\.){3}\d{1,3}\b|\d{9,13}/.test(candidate)) {
    return candidate;
  }
  return `api-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
}

async function readRequestBody(request) {
  if (["GET", "HEAD"].includes(String(request.method || "GET").toUpperCase())) {
    return undefined;
  }

  const declaredLength = Number.parseInt(readHeader(request.headers, "content-length"), 10);
  if (Number.isFinite(declaredLength) && declaredLength > MAX_REQUEST_BODY_BYTES) {
    throw new GatewayRequestError(413, "request_too_large");
  }

  if (Buffer.isBuffer(request.body)) {
    if (request.body.length > MAX_REQUEST_BODY_BYTES) {
      throw new GatewayRequestError(413, "request_too_large");
    }
    return request.body;
  }
  if (typeof request.body === "string") {
    const body = Buffer.from(request.body);
    if (body.length > MAX_REQUEST_BODY_BYTES) {
      throw new GatewayRequestError(413, "request_too_large");
    }
    return body;
  }
  if (request.body && typeof request.body === "object") {
    const body = Buffer.from(JSON.stringify(request.body));
    if (body.length > MAX_REQUEST_BODY_BYTES) {
      throw new GatewayRequestError(413, "request_too_large");
    }
    return body;
  }
  if (!request[Symbol.asyncIterator]) return undefined;

  const chunks = [];
  let total = 0;
  for await (const chunk of request) {
    const value = Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk);
    total += value.length;
    if (total > MAX_REQUEST_BODY_BYTES) {
      throw new GatewayRequestError(413, "request_too_large");
    }
    chunks.push(value);
  }
  return chunks.length ? Buffer.concat(chunks) : undefined;
}

function upstreamHeaders(request, correlationId) {
  const headers = { "x-request-id": correlationId };
  for (const name of ["accept", "authorization", "content-type", "if-none-match", "user-agent"]) {
    const value = readHeader(request.headers, name);
    if (value) headers[name] = value;
  }
  return headers;
}

function copyResponseHeaders(upstream, response) {
  for (const name of ["content-type", "cache-control", "etag", "last-modified"]) {
    const value = upstream.headers.get(name);
    if (value) response.setHeader(name, value);
  }
}

function publicDetail(status) {
  if (status === 400) return "The API rejected the request.";
  if (status === 401) return "Authentication is required.";
  if (status === 403) return "You are not allowed to use this API route.";
  if (status === 404) return "The requested API route was not found.";
  if (status === 405) return "Method not allowed.";
  if (status === 413) return "The request is too large.";
  if (status === 422) return "The API rejected the request data.";
  if (status === 429) return "The API is busy. Try again shortly.";
  if (status === 504) return "The API request timed out. Try again shortly.";
  return "Service is temporarily unavailable.";
}

function sendGatewayError(response, status, code, correlationId) {
  response.setHeader("x-request-id", correlationId);
  return response.status(status).json({
    status: "error",
    code,
    detail: publicDetail(status),
    correlation_id: correlationId,
  });
}

class GatewayRequestError extends Error {
  constructor(status, code) {
    super(code);
    this.name = "GatewayRequestError";
    this.status = status;
    this.code = code;
  }
}

async function proxyRequest(request, response, correlationId) {
  const target = requestPath(request);
  if (!target) {
    return sendGatewayError(response, 404, "route_not_available", correlationId);
  }
  if (!methodAllowed(request.method, target)) {
    response.setHeader("Allow", [...allowedMethods(target), "OPTIONS"].join(", "));
    return sendGatewayError(response, 405, "method_not_allowed", correlationId);
  }
  if (adminTokenRequired(target) && !hasBearerToken(request)) {
    return sendGatewayError(response, 401, "authentication_required", correlationId);
  }
  if (!BACKEND_ORIGIN) {
    return sendGatewayError(response, 503, "backend_not_configured", correlationId);
  }

  let body;
  try {
    body = await readRequestBody(request);
  } catch (error) {
    if (error instanceof GatewayRequestError) {
      return sendGatewayError(response, error.status, error.code, correlationId);
    }
    return sendGatewayError(response, 400, "invalid_request_body", correlationId);
  }

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), BACKEND_TIMEOUT_MS);
  try {
    const upstream = await fetch(`${BACKEND_ORIGIN}${target}`, {
      method: request.method,
      headers: upstreamHeaders(request, correlationId),
      body,
      redirect: "manual",
      signal: controller.signal,
    });
    const upstreamId = safeCorrelationIdFor(request, upstream.headers.get("x-request-id") || "");
    response.setHeader("x-request-id", upstreamId);

    if (!upstream.ok) {
      const status = upstream.status >= 400 && upstream.status <= 599 ? upstream.status : 502;
      const code = status < 500 ? "upstream_request_rejected" : "backend_unavailable";
      return sendGatewayError(response, status, code, upstreamId);
    }

    const responseBody = Buffer.from(await upstream.arrayBuffer());
    copyResponseHeaders(upstream, response);
    return response.status(upstream.status).send(responseBody);
  } catch {
    if (controller.signal.aborted) {
      return sendGatewayError(response, 504, "backend_timeout", correlationId);
    }
    return sendGatewayError(response, 502, "backend_unreachable", correlationId);
  } finally {
    clearTimeout(timeoutId);
  }
}

export default async function handler(request, response) {
  const cors = applyCorsPolicy(request, response, {
    methods: "GET, POST, DELETE, OPTIONS",
  });
  if (!cors.allowed) {
    return response.status(403).json({
      status: "error",
      code: "cors_origin_forbidden",
      detail: "Origin is not allowed.",
    });
  }

  const correlationId = safeCorrelationIdFor(request);
  const rawGitCommit = process.env.VERCEL_GIT_COMMIT_SHA || "";
  const gitCommit = /^[0-9a-f]{40}$/i.test(rawGitCommit) ? rawGitCommit.slice(0, 7) : "";
  if (gitCommit) response.setHeader("X-Deploy-SHA", gitCommit);
  if (request.method === "OPTIONS") return response.status(204).end();

  let requestUrl;
  try {
    requestUrl = new URL(request.url || "/", "https://gateway.invalid");
  } catch {
    return sendGatewayError(response, 400, "invalid_request_url", correlationId);
  }
  if (request.method === "GET"
    && requestUrl.pathname === "/api/index"
    && !requestUrl.searchParams.has("path")) {
    if (!BACKEND_ORIGIN) {
      return sendGatewayError(response, 503, "backend_not_configured", correlationId);
    }
    return response.status(200).json({
      status: "ok",
      service: "HoroConsultant Vercel Gateway",
    });
  }

  return proxyRequest(request, response, correlationId);
}
