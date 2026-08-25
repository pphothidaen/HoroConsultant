// api/health.js -- Vercel health gateway for the Azure Container Apps origin.
import {
  correlationIdFor,
  proxyToAzure,
  sendPublicError,
  setCorsHeaders,
} from "./gateway.js";

export default async function handler(req, res) {
  const cors = setCorsHeaders(res, "GET, OPTIONS", req);
  if (!cors.allowed) return res.status(403).end();
  if (req.method === "OPTIONS") return res.status(204).end();

  const correlationId = correlationIdFor(req);
  if (req.method !== "GET") {
    return sendPublicError(res, 405, correlationId, "Method not allowed.");
  }
  return proxyToAzure(req, res, "health", correlationId);
}
