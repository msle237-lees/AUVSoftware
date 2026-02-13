"""
FastAPI app entrypoint for AUVSoftware.
"""

from fastapi import FastAPI

from auvsoftware.api.routes.runs import router as runs_router
from auvsoftware.api.routes.imu import router as imu_router
from auvsoftware.api.routes.depth import router as depth_router
from auvsoftware.api.routes.power import router as power_router
from auvsoftware.api.routes.motor import router as motor_router
from auvsoftware.api.routes.servo import router as servo_router
from auvsoftware.api.routes.inputs import router as inputs_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="AUVSoftware API",
        version="0.1.0",
    )

    app.include_router(runs_router, prefix="/runs", tags=["runs"])
    app.include_router(imu_router, prefix="/imu", tags=["imu"])
    app.include_router(depth_router, prefix="/depth", tags=["depth"])
    app.include_router(power_router, prefix="/power", tags=["power"])
    app.include_router(motor_router, prefix="/motor", tags=["motor"])
    app.include_router(servo_router, prefix="/servo", tags=["servo"])
    app.include_router(inputs_router, prefix="/inputs", tags=["inputs"])

    return app


app = create_app()