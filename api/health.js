// api/health.js -- Vercel health gateway for the Azure Container Apps origin.
const AZURE_API_ORIGIN = (process.env.AZURE_API_ORIGIN || "").replace(/\/$/, "");

export default async function handler(req, res) {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "GET, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With");
  if (req.method === "OPTIONS") return res.status(204).end();
  if (req.method !== "GET") return res.status(405).json({ error: "Method not allowed" });
  if (!AZURE_API_ORIGIN) return res.status(503).json({ error: "Azure API origin is not configured" });

  try {
    const response = await fetch(`${AZURE_API_ORIGIN}/health`, { cache: "no-store" });
    const body = Buffer.from(await response.arrayBuffer());
    const contentType = response.headers.get("content-type");
    if (contentType) res.setHeader("content-type", contentType);
    return res.status(response.status).send(body);
  } catch (error) {
    return res.status(502).json({ error: `Azure health request failed: ${error.message}` });
  }
}
