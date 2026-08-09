// api/health.js — Dedicated Vercel Serverless Health Check Endpoint
export default function handler(req, res) {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Credentials", "true");
  res.setHeader("Access-Control-Allow-Methods", "GET, POST, OPTIONS, PUT, DELETE");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform");

  if (req.method === "OPTIONS") {
    return res.status(204).end();
  }

  return res.status(200).json({
    status: "ok",
    service: "Computational Metaphysics Engine",
    version: "1.0.0",
    gateway: "vercel-edge",
    timestamp: new Date().toISOString()
  });
}
