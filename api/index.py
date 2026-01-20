from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import json
import numpy as np

app = FastAPI()
@app.get("/")
def health():
    return {"status": "ok"}

# Enable CORS for POST requests from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST"],
    allow_headers=["*"],
)

# Load telemetry data
with open("telemetry.json", "r") as f:
    DATA = json.load(f)

@app.post("/analytics")
def analytics(payload: dict):
    regions = payload["regions"]
    threshold = payload["threshold_ms"]

    response = {}

    for region in regions:
        records = [r for r in DATA if r["region"] == region]

        latencies = [r["latency_ms"] for r in records]
        uptimes = [r["uptime_pct"] for r in records]

        response[region] = {
            "avg_latency": round(float(np.mean(latencies)), 2),
            "p95_latency": round(float(np.percentile(latencies, 95)), 2),
            "avg_uptime": round(float(np.mean(uptimes)), 2),
            "breaches": sum(1 for l in latencies if l > threshold)
        }

    return response

