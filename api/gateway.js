const AZURE_API_ORIGIN = (process.env.AZURE_API_ORIGIN || "").replace(/\/$/, "");
const SERVICE_UNAVAILABLE = "Service is temporarily unavailable.";
const DEFAULT_UPSTREAM_TIMEOUT_MS = 25_000;
const MAX_UPSTREAM_TIMEOUT_MS = 60_000;

const ALLOWED_PATHS = [
  /^api(?:\/|$)/,
  /^admin(?:\/|$)/,
  /^hitl(?:\/|$)/,
  /^hitl-studio$/,
  /^docs(?:\/|$)/,
  /^redoc$/,
  /^openapi\.json$/,
  /^metrics(?:\/|$)/,
  /^v1(?:\/|$)/,
  /^bazi(?:\/|$)/,
];

function configuredUpstreamTimeoutMs() {
  const configured = Number.parseInt(process.env.AZURE_API_TIMEOUT_MS || "", 10);
  if (!Number.isFinite(configured) || configured <= 0) return DEFAULT_UPSTREAM_TIMEOUT_MS;
  return Math.min(configured, MAX_UPSTREAM_TIMEOUT_MS);
}

const UPSTREAM_TIMEOUT_MS = configuredUpstreamTimeoutMs();

function readHeader(headers = {}, name) {
  const expected = name.toLowerCase();
  const entry = Object.entries(headers).find(([key]) => key.toLowerCase() === expected);
  return entry ? String(entry[1]) : "";
}

function validCorrelationId(value) {
  return /^[A-Za-z0-9._:-]{1,128}$/.test(value);
}

export function correlationIdFor(req, upstreamId = "") {
  const candidate = upstreamId || readHeader(req.headers, "x-request-id");
  if (validCorrelationId(candidate)) return candidate;
  return `gw-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
}

export function setCorsHeaders(res, methods) {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", methods);
  res.setHeader("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With, X-Request-ID");
}

export function sendPublicError(res, status, correlationId, detail = SERVICE_UNAVAILABLE) {
  res.setHeader("x-request-id", correlationId);
  return res.status(status).json({ detail, correlation_id: correlationId });
}

function decodedGatewayPath(rawPath) {
  if (typeof rawPath !== "string" || !rawPath || rawPath.length > 2048) return null;

  let decoded = rawPath;
  for (let pass = 0; pass < 4; pass += 1) {
    try {
      const next = decodeURIComponent(decoded);
      if (next === decoded) break;
      decoded = next;
    } catch {
      return null;
    }
  }

  try {
    // More nested escaping than the bounded decode pass is not a public route.
    if (decodeURIComponent(decoded) !== decoded) return null;
  } catch {
    return null;
  }

  return decoded;
}

export function normalizeGatewayPath(rawPath) {
  const path = decodedGatewayPath(rawPath);
  if (!path
    || path.startsWith("/")
    || path.includes("\\")
    || path.includes("//")
    || /[\u0000-\u001F\u007F?#]/.test(path)
    || !/^[A-Za-z0-9._~!$&'()*+,;=:@/-]+$/.test(path)) {
    return null;
  }

  try {
    const normalized = new URL(`https://gateway.invalid/${path}`).pathname.slice(1);
    if (normalized !== path) return null;
  } catch {
    return null;
  }

  return ALLOWED_PATHS.some(pattern => pattern.test(path)) ? path : null;
}

export function isAllowedGatewayPath(path) {
  return normalizeGatewayPath(path) !== null;
}

function upstreamHeaders(req, correlationId) {
  const headers = { "x-request-id": correlationId };
  for (const name of ["accept", "content-type", "authorization"]) {
    const value = readHeader(req.headers, name);
    if (value) headers[name] = value;
  }
  return headers;
}

function upstreamUrl(path, query) {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(query || {})) {
    if (key === "path" || value === undefined) continue;
    for (const item of Array.isArray(value) ? value : [value]) search.append(key, String(item));
  }
  const suffix = search.size ? `?${search.toString()}` : "";
  return `${AZURE_API_ORIGIN}/${path}${suffix}`;
}

function requestBody(req) {
  if (["GET", "HEAD"].includes(req.method)) return undefined;
  if (typeof req.body === "string" || Buffer.isBuffer(req.body)) return req.body;
  return JSON.stringify(req.body ?? {});
}

function safePublicText(value, limit = 240) {
  if (typeof value !== "string") return null;
  const candidate = value.trim();
  if (!candidate || candidate.length > limit
    || /https?:\/\/|localhost|azure|traceback|exception|stack trace|[\u0000-\u001F\u007F]/i.test(candidate)) {
    return null;
  }
  return candidate;
}

function safeValidationDetail(detail) {
  if (!Array.isArray(detail) || detail.length === 0 || detail.length > 50) return null;

  const issues = [];
  for (const issue of detail) {
    if (!issue || typeof issue !== "object" || Array.isArray(issue)) return null;
    const type = safePublicText(issue.type, 120);
    const message = safePublicText(issue.msg, 240);
    if (!type || !message || !Array.isArray(issue.loc) || issue.loc.length === 0 || issue.loc.length > 12) {
      return null;
    }
    const location = [];
    for (const segment of issue.loc) {
      if (Number.isInteger(segment) && segment >= 0 && segment < 10000) {
        location.push(segment);
      } else {
        const safeSegment = safePublicText(segment, 120);
        if (!safeSegment) return null;
        location.push(safeSegment);
      }
    }
    // Preserve FastAPI's stable machine-readable fields, not arbitrary echoed input/context.
    issues.push({ type, loc: location, msg: message });
  }
  return issues;
}

function safeDetail(payload, status) {
  const candidate = safePublicText(payload && payload.detail);
  if (status >= 400 && status < 500 && candidate) return candidate;
  if (status === 404) return "The requested API route was not found.";
  if (status === 401) return "Authentication is required.";
  if (status === 403) return "You are not allowed to use this API route.";
  if (status === 422) return "The API rejected the request data.";
  if (status === 429) return "The API is busy. Try again shortly.";
  return "The API is temporarily unavailable.";
}

function publicErrorBody(payload, status, correlationId) {
  const validationDetail = status === 422 && payload ? safeValidationDetail(payload.detail) : null;
  return {
    detail: validationDetail || safeDetail(payload, status),
    correlation_id: correlationId,
  };
}

async function errorPayload(response) {
  try {
    return await response.json();
  } catch {
    return null;
  }
}

export async function proxyToAzure(req, res, path, correlationId) {
  if (!AZURE_API_ORIGIN) return sendPublicError(res, 503, correlationId);

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), UPSTREAM_TIMEOUT_MS);
  try {
    const response = await fetch(upstreamUrl(path, req.query), {
      method: req.method,
      headers: upstreamHeaders(req, correlationId),
      body: requestBody(req),
      signal: controller.signal,
    });
    const upstreamCorrelationId = correlationIdFor(req, response.headers.get("x-request-id") || "");
    res.setHeader("x-request-id", upstreamCorrelationId);

    if (!response.ok) {
      const payload = await errorPayload(response);
      const bodyCorrelationId = payload && typeof payload.correlation_id === "string"
        ? correlationIdFor(req, payload.correlation_id)
        : upstreamCorrelationId;
      res.setHeader("x-request-id", bodyCorrelationId);
      return res.status(response.status).json(publicErrorBody(payload, response.status, bodyCorrelationId));
    }

    const body = Buffer.from(await response.arrayBuffer());
    const contentType = response.headers.get("content-type");
    if (contentType) res.setHeader("content-type", contentType);
    return res.status(response.status).send(body);
  } catch (error) {
    console.error("[ERROR] Azure gateway request failed", {
      correlation_id: correlationId,
      error_type: controller.signal.aborted ? "timeout" : (error && error.name ? error.name : "unknown"),
    });
    if (controller.signal.aborted) {
      return sendPublicError(res, 504, correlationId, "The API request timed out. Try again shortly.");
    }
    return sendPublicError(res, 502, correlationId);
  } finally {
    clearTimeout(timeoutId);
  }
}
