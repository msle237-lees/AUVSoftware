import routers
import uvicorn
from config import get_env
from deps import lifespan
from fastapi import FastAPI

app = FastAPI(title="AUV DB API", version="1.0.0", lifespan=lifespan)
app.include_router(routers.router)

@app.get("/")
async def root():
    return {"ok": True, "service": "AUV DB API"}

if __name__ == "__main__":
    host = get_env("AUV_HOST", default="0.0.0.0")
    port = int(get_env("AUV_PORT", default="8000"))
    uvicorn.run("run:app", host=host, port=port, reload=False)