// api/index.js - Vercel gateway for the production FastAPI service.
//
// Dynamic API calls must be forwarded to Azure Container Apps.  Returning a
// successful placeholder response here masks an unavailable backend and makes
// the browser treat invalid API payloads as valid responses.

const configuredBackend = process.env.HF_BACKEND_URL || "";
const BACKEND_URL = configuredBackend.replace(/\/$/, "");

const CORS_HEADERS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Credentials": "true",
  "Access-Control-Allow-Methods": "GET, POST, OPTIONS, PUT, PATCH, DELETE",
  "Access-Control-Allow-Headers":
    "Content-Type, Authorization, X-Requested-With, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, Referer, User-Agent",
};

function applyCors(response) {
  for (const [name, value] of Object.entries(CORS_HEADERS)) {
    response.setHeader(name, value);
  }
}

function getRequestTarget(request) {
  const requestUrl = new URL(request.url || "/", "http://localhost");
  const target = requestUrl.searchParams.get("path");
  if (!target || !target.startsWith("/") || target.startsWith("//")) {
    return null;
  }

  const query = new URLSearchParams(requestUrl.searchParams);
  query.delete("path");
  return `${target}${query.size ? `?${query.toString()}` : ""}`;
}

async function readRequestBody(request) {
  if (["GET", "HEAD"].includes(request.method || "GET")) {
    return undefined;
  }
  const chunks = [];
  for await (const chunk of request) {
    chunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk));
  }
  return chunks.length ? Buffer.concat(chunks) : undefined;
}

function forwardHeaders(request) {
  const forwarded = {};
  for (const name of ["accept", "authorization", "content-type", "if-none-match", "user-agent"]) {
    const value = request.headers[name];
    if (typeof value === "string") {
      forwarded[name] = value;
    }
  }
  return forwarded;
}

function copyResponseHeaders(upstream, response) {
  for (const name of ["content-type", "cache-control", "etag", "last-modified"]) {
    const value = upstream.headers.get(name);
    if (value) {
      response.setHeader(name, value);
    }
  }
}

async function proxyRequest(request, response) {
  const target = getRequestTarget(request);
  if (!target) {
    return response.status(400).json({
      status: "error",
      code: "invalid_gateway_target",
      message: "The gateway request target is missing or invalid.",
    });
  }
  if (!BACKEND_URL) {
    return response.status(503).json({
      status: "error",
      code: "backend_not_configured",
      message: "HF_BACKEND_URL is not configured for the Vercel gateway.",
    });
  }

  try {
    const upstream = await fetch(`${BACKEND_URL}${target}`, {
      method: request.method,
      headers: forwardHeaders(request),
      body: await readRequestBody(request),
      redirect: "manual",
    });
    copyResponseHeaders(upstream, response);
    const body = Buffer.from(await upstream.arrayBuffer());
    return response.status(upstream.status).send(body);
  } catch (error) {
    console.error("[ERROR] Vercel gateway backend request failed", error);
    return response.status(502).json({
      status: "error",
      code: "backend_unreachable",
      message: "The production backend could not be reached by the gateway.",
    });
  }
}

export default async function handler(request, response) {
  applyCors(response);
  if (request.method === "OPTIONS") {
    return response.status(204).end();
  }

  const requestUrl = new URL(request.url || "/", "http://localhost");
  if (request.method === "GET" && requestUrl.pathname === "/api/index" && !requestUrl.searchParams.get("path")) {
    return response.status(200).json({
      status: "ok",
      service: "HoroConsultant Vercel Gateway",
      backend_configured: Boolean(BACKEND_URL),
    });
  }
  return proxyRequest(request, response);
}
