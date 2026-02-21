from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from pathlib import Path
import json
import statistics

app = FastAPI()

# Proper CORS for Vercel + Grader
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load telemetry file
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "telemetry.json"

with open(DATA_FILE, "r") as f:
    telemetry = json.load(f)


class Input(BaseModel):
    regions: List[str]
    threshold_ms: int


@app.post("/")
def analyze(payload: Input):
    results = {}

    for region in payload.regions:
        rows = [r for r in telemetry if r["region"] == region]
        if not rows:
            continue

        lat = [r["latency_ms"] for r in rows]
        up = [r["uptime_pct"] for r in rows]

        avg_latency = statistics.mean(lat)

        # Correct p95
        s = sorted(lat)
        n = len(s)
        i = 0.95 * (n - 1)
        lo = int(i)
        hi = lo + 1
        frac = i - lo
        if hi < n:
            p95 = s[lo] + frac * (s[hi] - s[lo])
        else:
            p95 = s[lo]

        avg_uptime = statistics.mean(up)
        breaches = sum(1 for x in lat if x > payload.threshold_ms)

        results[region] = {
            "avg_latency": round(avg_latency, 2),
            "p95_latency": round(p95, 2),
            "avg_uptime": round(avg_uptime, 2),
            "breaches": breaches,
        }

    return {"regions": results}
