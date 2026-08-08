import sys
from pathlib import Path

# Add project root directory to sys.path for Vercel Serverless Lambda environment
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from project.main import app

# Export FastAPI app for Vercel Serverless Function
app = app
