import logging
import os
import time

import requests
from prometheus_client import Counter, Histogram, start_http_server
from sqlalchemy import create_engine, text

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("worker")

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./local.db")
INTERVAL = int(os.getenv("CHECK_INTERVAL_SECONDS", "30"))
METRICS_PORT = int(os.getenv("METRICS_PORT", "9100"))

CHECKS = Counter("statuswatch_checks_total", "Checks performed", ["result"])
LATENCY = Histogram("statuswatch_check_latency_seconds", "Check latency")


def check_url(url, timeout=5):
    """Return (status_code, latency_ms, ok) for one URL."""
    start = time.perf_counter()
    try:
        resp = requests.get(url, timeout=timeout)
        latency = (time.perf_counter() - start) * 1000
        return resp.status_code, round(latency, 1), resp.status_code < 400
    except requests.RequestException:
        latency = (time.perf_counter() - start) * 1000
        return None, round(latency, 1), False


def run_once(engine):
    with engine.begin() as conn:
        monitors = conn.execute(text("SELECT id, url FROM monitors")).all()
        for mid, url in monitors:
            code, latency, ok = check_url(url)
            CHECKS.labels(result="up" if ok else "down").inc()
            LATENCY.observe(latency / 1000)
            conn.execute(
                text("INSERT INTO checks (monitor_id, status_code, "
                     "latency_ms, ok, checked_at) VALUES "
                     "(:m, :c, :l, :ok, CURRENT_TIMESTAMP)"),
                {"m": mid, "c": code, "l": latency, "ok": ok},
            )
            log.info("checked %s -> %s (%.0f ms)", url, code, latency)


def main():
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    start_http_server(METRICS_PORT)
    log.info("worker started, interval=%ss", INTERVAL)
    while True:
        try:
            run_once(engine)
        except Exception as exc:  # DB not ready or tables missing yet
            log.warning("cycle failed: %s", exc)
        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
