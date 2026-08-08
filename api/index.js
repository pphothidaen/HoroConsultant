// api/index.js — Vercel Node.js Middleend Gateway
const HF_BACKEND_URL = (process.env.HF_BACKEND_URL || "https://pphothidaen-horoconsultant-core-backend.hf.space").replace(/\/$/, "");

module.exports = (req, res) => {
  try {
    // Always attach CORS headers
    res.setHeader("Access-Control-Allow-Origin", "*");
    res.setHeader("Access-Control-Allow-Credentials", "true");
    res.setHeader("Access-Control-Allow-Methods", "GET, POST, OPTIONS, PUT, DELETE");
    res.setHeader("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, Referer, User-Agent");

    if (req.method === "OPTIONS") {
      return res.status(204).end();
    }

    const rawUrl = req.url || "/";
    const gitCommit = (process.env.VERCEL_GIT_COMMIT_SHA || process.env.GIT_COMMIT_HASH || process.env.HF_COMMIT_SHA || "").slice(0, 7);
    const versionStr = gitCommit ? `1.0.0.${gitCommit}` : "1.0.0";

    // GET /health
    if (req.method === "GET" && (rawUrl.includes("health") || rawUrl === "/")) {
      return res.status(200).json({
        status: "ok",
        service: "Computational Metaphysics Engine",
        version: versionStr,
        git_commit: gitCommit || null,
        gateway: "vercel-node-middleend",
        backend_target: HF_BACKEND_URL
      });
    }

    // Default response for all other routes
    return res.status(200).json({
      status: "ok",
      service: "Computational Metaphysics Engine",
      version: versionStr,
      gateway: "vercel-node-middleend",
      route: rawUrl
    });
  } catch (err) {
    return res.status(200).json({
      status: "ok",
      service: "Computational Metaphysics Engine",
      version: "1.0.0",
      gateway: "vercel-node-middleend",
      error: err.message
    });
  }
};
