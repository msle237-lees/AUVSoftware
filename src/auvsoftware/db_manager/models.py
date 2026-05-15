from typing import Annotated, Optional

from pydantic import BaseModel, Field


# ---- inputs ----
class InputsCreate(BaseModel):
    TIMESTAMP: Optional[str] = Field(None, description="ISO8601 UTC string")
    SURGE: int; SWAY: int; HEAVE: int; ROLL: int; PITCH: int; YAW: int
    S1: Annotated[int, Field(ge=0, le=1)]; S2: Annotated[int, Field(ge=0, le=1)]
    S3: int

class InputsRead(InputsCreate):
    ID: int
    TIMESTAMP: str

# ---- outputs ----
class OutputsCreate(BaseModel):
    TIMESTAMP: Optional[str] = None
    MOTOR1: int; MOTOR2: int; MOTOR3: int; MOTOR4: int
    MOTOR5: int; MOTOR6: int; MOTOR7: int; MOTOR8: int
    S1: int; S2: int; S3: int

class OutputsRead(OutputsCreate):
    ID: int
    TIMESTAMP: str

# ---- depth ----
class DepthCreate(BaseModel):
    TIMESTAMP: Optional[str] = None
    DEPTH: float

class DepthRead(DepthCreate):
    ID: int
    TIMESTAMP: str

# ---- imu ----
class ImuCreate(BaseModel):
    TIMESTAMP: Optional[str] = None
    ACCEL_X: float; ACCEL_Y: float; ACCEL_Z: float
    GYRO_X: float;  GYRO_Y: float;  GYRO_Z: float
    MAG_X: float;   MAG_Y: float;   MAG_Z: float

class ImuRead(ImuCreate):
    ID: int
    TIMESTAMP: str

# ---- power_safety ----
class PowerSafetyCreate(BaseModel):
    TIMESTAMP: Optional[str] = None
    B1_VOLTAGE: int; B2_VOLTAGE: int; B3_VOLTAGE: int
    B1_CURRENT: int; B2_CURRENT: int; B3_CURRENT: int
    B1_TEMP: int;    B2_TEMP: int;    B3_TEMP: int

class PowerSafetyRead(PowerSafetyCreate):
    ID: int
    TIMESTAMP: str

# ---- pid_gains ----
class PidGainsCreate(BaseModel):
    TIMESTAMP: Optional[str] = None
    ROLL_KP: float;  ROLL_KI: float;  ROLL_KD: float
    PITCH_KP: float; PITCH_KI: float; PITCH_KD: float

class PidGainsRead(PidGainsCreate):
    ID: int
    TIMESTAMP: str

# ---- detections ----
class DetectionsCreate(BaseModel):
    TIMESTAMP: Optional[str] = None
    CAMERA: str
    CLASS_NAME: str
    CONFIDENCE: float
    BBOX_X: float
    BBOX_Y: float
    BBOX_W: float
    BBOX_H: float
    DISTANCE: float  # metres; -1.0 if unavailable

class DetectionsRead(DetectionsCreate):
    ID: int
    TIMESTAMP: str

# ---- list wrapper (shared) ----
class ListEnvelope(BaseModel):
    items: list
    total: int
    limit: int
    offset: int
