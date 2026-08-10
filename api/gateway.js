const AZURE_API_ORIGIN = (process.env.AZURE_API_ORIGIN || "").replace(/\/$/, "");
const SERVICE_UNAVAILABLE = "Service is temporarily unavailable.";

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

export function isAllowedGatewayPath(path) {
  return !path.split("/").some(segment => segment === "." || segment === "..")
    && ALLOWED_PATHS.some(pattern => pattern.test(path));
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

function safeDetail(payload, status) {
  const candidate = payload && typeof payload.detail === "string" ? payload.detail.trim() : "";
  if (status >= 400 && status < 500 && candidate && candidate.length <= 240
    && !/https?:\/\/|localhost|traceback|exception|stack trace/i.test(candidate)) {
    return candidate;
  }
  if (status === 404) return "The requested API route was not found.";
  if (status === 401) return "Authentication is required.";
  if (status === 403) return "You are not allowed to use this API route.";
  if (status === 422) return "The API rejected the request data.";
  if (status === 429) return "The API is busy. Try again shortly.";
  return "The API is temporarily unavailable.";
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

  try {
    const response = await fetch(upstreamUrl(path, req.query), {
      method: req.method,
      headers: upstreamHeaders(req, correlationId),
      body: requestBody(req),
    });
    const upstreamCorrelationId = correlationIdFor(req, response.headers.get("x-request-id") || "");
    res.setHeader("x-request-id", upstreamCorrelationId);

    if (!response.ok) {
      const payload = await errorPayload(response);
      const bodyCorrelationId = payload && typeof payload.correlation_id === "string"
        ? correlationIdFor(req, payload.correlation_id)
        : upstreamCorrelationId;
      res.setHeader("x-request-id", bodyCorrelationId);
      return res.status(response.status).json({
        detail: safeDetail(payload, response.status),
        correlation_id: bodyCorrelationId,
      });
    }

    const body = Buffer.from(await response.arrayBuffer());
    const contentType = response.headers.get("content-type");
    if (contentType) res.setHeader("content-type", contentType);
    return res.status(response.status).send(body);
  } catch (error) {
    console.error("[ERROR] Azure gateway request failed", {
      correlation_id: correlationId,
      error_type: error && error.name ? error.name : "unknown",
    });
    return sendPublicError(res, 502, correlationId);
  }
}
