from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import build, dock, jobs, surface, vaults

app = FastAPI(
    title="SCUBA Ideaverse",
    version="0.3.0",
    description="Your research world, mapped and connected.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(vaults.router)
app.include_router(dock.router)
app.include_router(surface.router)
app.include_router(build.router)
app.include_router(jobs.router)


@app.get("/health")
def health():
    return {"status": "ok", "product": "SCUBA Ideaverse"}


@app.get("/dive_computer")
def dive_computer():
    from app.services.vault_manager import VaultManager
    return {"vaults": VaultManager().list_vaults()}
