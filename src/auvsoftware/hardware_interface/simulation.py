import logging
import time

import numpy as np

from auvsoftware.quick_request import AUVClient

_log = logging.getLogger(__name__)

_NEUTRAL: int = 127
_SCENARIO = "SimpleUnderwater-Hovering"

# HoveringAUV command: [vert1, vert2, vert3, vert4, horiz1, horiz2, horiz3, horiz4]
# Map our 0-255 motor values (127=neutral) to HoloOcean thrust by centering around zero.
_SCALE: float = 100.0 / 128.0


def _to_thrust(value: int) -> float:
    return (value - _NEUTRAL) * _SCALE


class SimulationController:
    def __init__(self) -> None:
        import holoocean

        self._client = AUVClient()
        self._env = holoocean.make(_SCENARIO)
        _log.info("HoloOcean environment '%s' ready", _SCENARIO)

    def _command_from_db(self) -> np.ndarray:
        data = self._client.latest("outputs")
        if data is None:
            return np.zeros(8, dtype=float)
        # HoveringAUV: [vert1..4, horiz1..4]
        # MOTOR1-4 → vertical thrusters; MOTOR5-8 → horizontal thrusters.
        return np.array(
            [_to_thrust(data.get(f"MOTOR{i}", _NEUTRAL)) for i in range(1, 9)],
            dtype=float,
        )

    def _post_state(self, state: dict) -> None:
        if "IMUSensor" in state:
            imu = state["IMUSensor"]
            self._client.post(
                "imu",
                ACCEL_X=float(imu[0, 0]), ACCEL_Y=float(imu[0, 1]), ACCEL_Z=float(imu[0, 2]),
                GYRO_X=float(imu[1, 0]),  GYRO_Y=float(imu[1, 1]),  GYRO_Z=float(imu[1, 2]),
                MAG_X=0.0, MAG_Y=0.0, MAG_Z=0.0,
            )
        if "LocationSensor" in state:
            loc = state["LocationSensor"]
            self._client.post("depth", DEPTH=float(-loc[2]))

    def run(self) -> None:
        try:
            while True:
                cmd = self._command_from_db()
                state = self._env.step(cmd)
                self._post_state(state)
                time.sleep(0.02)  # ~50 Hz
        except KeyboardInterrupt:
            pass
        finally:
            self._env.close()
            _log.info("HoloOcean environment closed")
