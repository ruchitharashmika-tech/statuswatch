from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from prometheus_client import make_asgi_app
from pydantic import BaseModel, HttpUrl
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import Base, Check, Monitor, SessionLocal, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    yield


app = FastAPI(title="StatusWatch API", lifespan=lifespan)
app.mount("/metrics", make_asgi_app())


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class MonitorIn(BaseModel):
    name: str
    url: HttpUrl


def latest_check(db: Session, monitor_id: int):
    stmt = (select(Check).where(Check.monitor_id == monitor_id)
            .order_by(Check.id.desc()).limit(1))
    return db.execute(stmt).scalar_one_or_none()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/monitors", status_code=201)
def create_monitor(body: MonitorIn, db: Session = Depends(get_db)):
    m = Monitor(name=body.name, url=str(body.url))
    db.add(m)
    db.commit()
    db.refresh(m)
    return {"id": m.id, "name": m.name, "url": m.url}


@app.get("/api/monitors")
def list_monitors(db: Session = Depends(get_db)):
    out = []
    for m in db.execute(select(Monitor).order_by(Monitor.id)).scalars():
        c = latest_check(db, m.id)
        out.append({
            "id": m.id,
            "name": m.name,
            "url": m.url,
            "status": None if c is None else ("up" if c.ok else "down"),
            "latency_ms": None if c is None else c.latency_ms,
            "last_checked": None if c is None else c.checked_at.isoformat(),
        })
    return out


@app.delete("/api/monitors/{monitor_id}", status_code=204)
def delete_monitor(monitor_id: int, db: Session = Depends(get_db)):
    m = db.get(Monitor, monitor_id)
    if m is None:
        raise HTTPException(status_code=404, detail="Monitor not found")
    db.query(Check).filter(Check.monitor_id == monitor_id).delete()
    db.delete(m)
    db.commit()


@app.get("/api/monitors/{monitor_id}/checks")
def list_checks(monitor_id: int, limit: int = 20,
                db: Session = Depends(get_db)):
    if db.get(Monitor, monitor_id) is None:
        raise HTTPException(status_code=404, detail="Monitor not found")
    stmt = (select(Check).where(Check.monitor_id == monitor_id)
            .order_by(Check.id.desc()).limit(min(limit, 100)))
    return [
        {"status_code": c.status_code, "latency_ms": c.latency_ms,
         "ok": c.ok, "checked_at": c.checked_at.isoformat()}
        for c in db.execute(stmt).scalars()
    ]
