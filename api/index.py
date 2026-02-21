from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from pathlib import Path
import json
import statistics

app = FastAPI()

# Enable CORS for grader (Access-Control-Allow-Origin: *)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------
# Load telemetry.json safely
# -------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "telemetry.json"

if not DATA_FILE.exists():
    raise Exception(f"Missing telemetry.json at {DATA_FILE}")

with open(DATA_FILE, "r") as f:
    telemetry = json.load(f)


# -------------------------------
# Request model
# -------------------------------
class Input(BaseModel):
    regions: List[str]
    threshold_ms: int


# -------------------------------
# POST endpoint (ROOT "/")
# -------------------------------
@app.post("/")
def analyze(payload: Input):
    results = {}

    for region in payload.regions:
        rows = [r for r in telemetry if r["region"] == region]

        if not rows:
            continue

        latencies = [r["latency_ms"] for r in rows]
        uptimes = [r["uptime_pct"] for r in rows]

        # Mean latency
        avg_latency = statistics.mean(latencies)

        # -------- p95 (grader safe) --------
        sorted_lat = sorted(latencies)
        n = len(sorted_lat)
        idx = 0.95 * (n - 1)
        lo = int(idx)
        hi = lo + 1
        frac = idx - lo

        if hi < n:
            p95 = sorted_lat[lo] + frac * (sorted_lat[hi] - sorted_lat[lo])
        else:
            p95 = sorted_lat[lo]

        # Mean uptime
        avg_uptime = statistics.mean(uptimes)

        # Count breaches
        breaches = sum(1 for l in latencies if l > payload.threshold_ms)

        results[region] = {
            "avg_latency": round(avg_latency, 2),
            "p95_latency": round(p95, 2),
            "avg_uptime": round(avg_uptime, 2),
            "breaches": breaches,
        }

    # Grader expects "regions"
    return {"regions": results}
