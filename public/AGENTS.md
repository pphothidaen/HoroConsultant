# public/ — Static Frontend Assets

## Purpose
Static HTML/CSS/JS files served by Vercel as the production UI.

## Key Files
- `public/admin.html` — Admin Panel (Knowledge Source Manager, Gray-Zone, Fine-Tune Pipeline)
- `public/index.html` — Main Web UI Dashboard
- `public/charts/` — Chart assets

## Architecture
- Pure HTML5/CSS3 (Glassmorphism dark theme)
- No build step — files are served directly by Vercel
- API calls go through `/api/index?path=...` rewrites

## Environment
- `window.API_BASE_URL` can override the API base URL
- On `static.hf.space`, defaults to `https://horo-consultant-psi.vercel.app`
