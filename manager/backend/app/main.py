from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import build, dock, jobs, settings, surface, vaults

app = FastAPI(
    title="Portolan",
    version="0.6.0",
    description="Read what you dock. Chart the connections.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(settings.router)
app.include_router(vaults.router)
app.include_router(dock.router)
app.include_router(surface.router)
app.include_router(build.router)
app.include_router(jobs.router)


@app.get("/health")
def health():
    return {"status": "ok", "product": "Portolan"}


@app.get("/dive_computer")
def dive_computer():
    from app.deps import vault_manager
    return {"vaults": vault_manager.list_vaults()}
