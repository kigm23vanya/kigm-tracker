from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import achievements, assignments, auth, events, leaderboard, profile, sync
from app.core.config import settings
from app.core.database import Base, SessionLocal, engine
from app.db.bootstrap import seed_initial_data
from app import models  # noqa: F401

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_initial_data(db)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "env": settings.app_env}


app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(assignments.router)
app.include_router(events.router)
app.include_router(achievements.router)
app.include_router(leaderboard.router)
app.include_router(sync.router)
