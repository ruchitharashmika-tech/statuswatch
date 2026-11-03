import os

os.environ["DATABASE_URL"] = "sqlite://"

from fastapi.testclient import TestClient  # noqa: E402

from app.db import Check, SessionLocal  # noqa: E402
from app.main import app  # noqa: E402


def test_health():
    with TestClient(app) as client:
        assert client.get("/health").json() == {"status": "ok"}


def test_monitor_lifecycle():
    with TestClient(app) as client:
        r = client.post("/api/monitors",
                        json={"name": "Example", "url": "https://example.com"})
        assert r.status_code == 201
        mid = r.json()["id"]

        listed = client.get("/api/monitors").json()
        assert any(m["id"] == mid and m["status"] is None for m in listed)

        with SessionLocal() as db:
            db.add(Check(monitor_id=mid, status_code=200,
                         latency_ms=42.0, ok=True))
            db.commit()

        listed = client.get("/api/monitors").json()
        assert [m for m in listed if m["id"] == mid][0]["status"] == "up"
        assert len(client.get(f"/api/monitors/{mid}/checks").json()) == 1

        assert client.delete(f"/api/monitors/{mid}").status_code == 204
        assert client.get(f"/api/monitors/{mid}/checks").status_code == 404


def test_invalid_url_rejected():
    with TestClient(app) as client:
        r = client.post("/api/monitors", json={"name": "x", "url": "nope"})
        assert r.status_code == 422
