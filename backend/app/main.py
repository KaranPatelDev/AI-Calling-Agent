from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, calls, settings, uploads, voice
from app.scheduler import scheduler

app = FastAPI(title="Calling Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(calls.router)
app.include_router(voice.router)
app.include_router(uploads.router)
app.include_router(settings.router)


@app.on_event("startup")
def start_scheduler():
    scheduler.start()


@app.on_event("shutdown")
def stop_scheduler():
    scheduler.shutdown(wait=False)


@app.get("/health")
def health():
    return {"ok": True}
