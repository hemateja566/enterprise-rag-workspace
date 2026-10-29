"""Smoke test the FastAPI app with TestClient (no server needed)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient  # noqa: E402
from api.main import app  # noqa: E402

client = TestClient(app)

health = client.get("/health")
print("health:", health.status_code, health.json())

r = client.post("/triage", json={
    "subject": "SSO broken for new users",
    "body": "SAML login fails since this morning for all new hires. Production impact, no workaround.",
})
print("triage:", r.status_code)
d = r.json()
for k in ("product", "category", "urgency", "recommended_team", "engine", "known_issue_match"):
    print(f"  {k}: {d[k]}")
print("  kb:", [m["path"] for m in d["kb_matches"]][:2])

b = client.get("/account-brief/ACC-3336")
print("brief:", b.status_code)
bj = b.json()
print("  summary:", bj["executive_summary"][:120], "...")
print("  risks:", [(f["signal_type"], f["severity"]) for f in bj["open_risks"]])
print("  talking_points:", len(bj["talking_points"]))
print("  hash:", bj["deterministic_rerun_hash"])

s = client.post("/triage/stream", json={
    "subject": "test streaming",
    "body": "Simple test of the NDJSON streaming endpoint for dashboards.",
})
print("stream:", s.status_code, "| first line keys:", list(s.json().splitlines() and __import__("json").loads(s.text.splitlines()[0]).keys()))
