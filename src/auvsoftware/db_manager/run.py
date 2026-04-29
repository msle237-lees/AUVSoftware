from fastapi import FastAPI

from src.auvsoftware.db_manager.deps import lifespan
import src.auvsoftware.db_manager.routers as routers


app = FastAPI(title="AUV DB API", version="1.0.0", lifespan=lifespan)

# Register all routes
app.include_router(routers.router)


@app.get("/")
async def root():
    return {"ok": True, "service": "AUV DB API"}
