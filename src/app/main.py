from fastapi import FastAPI
from .routes.practice import router as practice_router

app = FastAPI(title="Practice Service", version="1.0.0")

app.include_router(practice_router, prefix="/practice", tags=["practice"])

@app.get("/")
def root():
    return {"ok": True}
