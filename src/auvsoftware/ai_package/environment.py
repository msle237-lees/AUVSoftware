"""
AUV gym-style environment backed entirely by the database.

State  : latest rows from depth, imu, detections tables
Action : np.ndarray of shape (9,) in [-1, 1], written to the inputs table
         indices: [SURGE, SWAY, HEAVE, ROLL, PITCH, YAW, S1, S2, S3]
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

from auvsoftware.quick_request import AUVClient, AUVRequestError

INPUT_SCALE = 100       # inputs stored as ints in [-100, 100]
MAX_DETECTIONS = 3      # top-K detections by confidence
DETECTION_FEATURES = 6  # confidence, bbox_x, bbox_y, bbox_w, bbox_h, distance

STATE_DIM = (
    1                               # depth
    + 9                             # imu: accel xyz, gyro xyz, mag xyz
    + MAX_DETECTIONS * DETECTION_FEATURES
)
ACTION_DIM = 9  # SURGE SWAY HEAVE ROLL PITCH YAW S1 S2 S3


@dataclass
class WorldState:
    depth: float = 0.0
    accel_x: float = 0.0
    accel_y: float = 0.0
    accel_z: float = 9.81
    gyro_x: float = 0.0
    gyro_y: float = 0.0
    gyro_z: float = 0.0
    mag_x: float = 0.0
    mag_y: float = 0.0
    mag_z: float = 0.0
    detections: list[dict] = field(default_factory=list)

    def to_vector(self) -> np.ndarray:
        vec: list[float] = [
            self.depth,
            self.accel_x, self.accel_y, self.accel_z,
            self.gyro_x,  self.gyro_y,  self.gyro_z,
            self.mag_x,   self.mag_y,   self.mag_z,
        ]
        sorted_det = sorted(
            self.detections,
            key=lambda d: d.get("CONFIDENCE", 0.0),
            reverse=True,
        )
        for i in range(MAX_DETECTIONS):
            if i < len(sorted_det):
                d = sorted_det[i]
                vec += [
                    d.get("CONFIDENCE", 0.0),
                    d.get("BBOX_X", 0.0),
                    d.get("BBOX_Y", 0.0),
                    d.get("BBOX_W", 0.0),
                    d.get("BBOX_H", 0.0),
                    d.get("DISTANCE", 0.0),
                ]
            else:
                vec += [0.0] * DETECTION_FEATURES
        return np.array(vec, dtype=np.float32)


class AUVEnvironment:
    """
    DB-backed environment compatible with the gym step/reset interface.

    reset() -> np.ndarray
    step(action) -> (state, reward, terminated, truncated, info)

    Actions are np.ndarray of shape (9,) clipped to [-1, 1]:
      [0-5]  SURGE/SWAY/HEAVE/ROLL/PITCH/YAW  multiplied by INPUT_SCALE → int
      [6]    S1  : 1 if >= 0 else 0
      [7]    S2  : 1 if >= 0 else 0
      [8]    S3  : mapped from [-1,1] → [0, 255]
    """

    state_dim  = STATE_DIM
    action_dim = ACTION_DIM

    def __init__(
        self,
        client: Optional[AUVClient] = None,
        reward_fn: Optional["RewardFunction"] = None,  # noqa: F821
        max_steps: int = 500,
        step_delay: float = 0.05,
    ) -> None:
        from auvsoftware.ai_package.reward import DefaultReward
        self._client     = client or AUVClient()
        self._reward_fn  = reward_fn or DefaultReward()
        self._max_steps  = max_steps
        self._step_delay = step_delay
        self._step_count = 0
        self._prev_state: Optional[WorldState] = None

    def reset(self) -> np.ndarray:
        self._step_count = 0
        self._reward_fn.reset()
        state = self._fetch_state()
        self._prev_state = state
        return state.to_vector()

    def step(self, action: np.ndarray) -> tuple[np.ndarray, float, bool, bool, dict]:
        self._apply_action(action)
        if self._step_delay > 0:
            time.sleep(self._step_delay)
        state = self._fetch_state()
        reward = self._reward_fn.compute(state, self._prev_state)
        self._prev_state = state
        self._step_count += 1
        truncated  = self._step_count >= self._max_steps
        terminated = False
        return state.to_vector(), reward, terminated, truncated, {}

    def observation(self) -> np.ndarray:
        """Current state vector without stepping (for real-world init)."""
        return self._fetch_state().to_vector()

    def _fetch_state(self) -> WorldState:
        s = WorldState()
        try:
            row = self._client.latest("depth")
            if row:
                s.depth = float(row.get("DEPTH", 0.0))
        except AUVRequestError:
            pass
        try:
            row = self._client.latest("imu")
            if row:
                s.accel_x = float(row.get("ACCEL_X", 0.0))
                s.accel_y = float(row.get("ACCEL_Y", 0.0))
                s.accel_z = float(row.get("ACCEL_Z", 9.81))
                s.gyro_x  = float(row.get("GYRO_X",  0.0))
                s.gyro_y  = float(row.get("GYRO_Y",  0.0))
                s.gyro_z  = float(row.get("GYRO_Z",  0.0))
                s.mag_x   = float(row.get("MAG_X",   0.0))
                s.mag_y   = float(row.get("MAG_Y",   0.0))
                s.mag_z   = float(row.get("MAG_Z",   0.0))
        except AUVRequestError:
            pass
        try:
            page = self._client.list("detections", limit=MAX_DETECTIONS)
            s.detections = page.get("items", [])
        except AUVRequestError:
            pass
        return s

    def _apply_action(self, action: np.ndarray) -> None:
        a = np.clip(action, -1.0, 1.0)
        surge = int(round(float(a[0]) * INPUT_SCALE))
        sway  = int(round(float(a[1]) * INPUT_SCALE))
        heave = int(round(float(a[2]) * INPUT_SCALE))
        roll  = int(round(float(a[3]) * INPUT_SCALE))
        pitch = int(round(float(a[4]) * INPUT_SCALE))
        yaw   = int(round(float(a[5]) * INPUT_SCALE))
        s1    = 1 if float(a[6]) >= 0.0 else 0
        s2    = 1 if float(a[7]) >= 0.0 else 0
        s3    = int(np.clip(round((float(a[8]) + 1.0) * 127.5), 0, 255))
        try:
            self._client.post(
                "inputs",
                SURGE=surge, SWAY=sway, HEAVE=heave,
                ROLL=roll, PITCH=pitch, YAW=yaw,
                S1=s1, S2=s2, S3=s3,
            )
        except AUVRequestError:
            pass
