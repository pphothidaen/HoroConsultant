// api/index.js -- Vercel gateway for the Azure Container Apps API origin.
const AZURE_API_ORIGIN = (process.env.AZURE_API_ORIGIN || "").replace(/\/$/, "");

function setCorsHeaders(res) {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "GET, POST, OPTIONS, PUT, DELETE");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With");
}

function upstreamHeaders(req) {
  const headers = {};
  for (const name of ["accept", "content-type", "authorization", "x-request-id"]) {
    if (req.headers[name]) headers[name] = req.headers[name];
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
  return `${AZURE_API_ORIGIN}/api/${path}${suffix}`;
}

function requestBody(req) {
  if (["GET", "HEAD"].includes(req.method)) return undefined;
  if (typeof req.body === "string" || Buffer.isBuffer(req.body)) return req.body;
  return JSON.stringify(req.body ?? {});
}

export default async function handler(req, res) {
  setCorsHeaders(res);
  if (req.method === "OPTIONS") return res.status(204).end();

  if (!AZURE_API_ORIGIN) {
    return res.status(503).json({ error: "Azure API origin is not configured" });
  }

  const path = String(req.query?.path || "").replace(/^\//, "");
  if (!path) return res.status(404).json({ error: "API route was not provided" });

  try {
    const response = await fetch(upstreamUrl(path, req.query), {
      method: req.method,
      headers: upstreamHeaders(req),
      body: requestBody(req),
    });
    const body = Buffer.from(await response.arrayBuffer());
    const contentType = response.headers.get("content-type");
    if (contentType) res.setHeader("content-type", contentType);
    return res.status(response.status).send(body);
  } catch (error) {
    return res.status(502).json({ error: `Azure API request failed: ${error.message}` });
  }
}
