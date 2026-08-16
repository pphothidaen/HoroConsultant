// api/index.js -- closed Vercel gateway for public Azure Container Apps routes.
import {
  correlationIdFor,
  normalizeGatewayPath,
  proxyToAzure,
  sendPublicError,
  setCorsHeaders,
} from "./gateway.js";

export default async function handler(req, res) {
  setCorsHeaders(res, "GET, POST, OPTIONS, PUT, DELETE");
  if (req.method === "OPTIONS") return res.status(204).end();

  const correlationId = correlationIdFor(req);
  const path = normalizeGatewayPath(String(req.query?.path || "").replace(/^\//, ""));
  if (!path) {
    return sendPublicError(res, 404, correlationId, "The requested API route was not found.");
  }
  return proxyToAzure(req, res, path, correlationId);
}
