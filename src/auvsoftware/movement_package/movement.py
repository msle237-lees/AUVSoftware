import logging
import math
import signal
import time

from auvsoftware.logging_config import setup_logging
from auvsoftware.movement_package.mixer import mix
from auvsoftware.movement_package.pid import PIDController
from auvsoftware.quick_request import AUVClient

_RATE: float = 0.05                # 20 Hz control loop
_GAINS_RELOAD_INTERVAL: float = 2.0  # seconds between DB gain polls
_INPUT_SCALE: float = 100.0        # input DB values are in [-100, 100]

_log = logging.getLogger(__name__)


class MovementController:
    def __init__(self) -> None:
        self._client = AUVClient()
        self._roll_pid  = PIDController(kp=1.0, ki=0.0, kd=0.1)
        self._pitch_pid = PIDController(kp=1.0, ki=0.0, kd=0.1)
        self._last_gains_reload: float = 0.0

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _reload_gains(self) -> None:
        try:
            data = self._client.latest("pid_gains")
        except Exception:
            return
        if data is None:
            return
        self._roll_pid.set_gains(
            float(data.get("ROLL_KP",  self._roll_pid.kp)),
            float(data.get("ROLL_KI",  self._roll_pid.ki)),
            float(data.get("ROLL_KD",  self._roll_pid.kd)),
        )
        self._pitch_pid.set_gains(
            float(data.get("PITCH_KP", self._pitch_pid.kp)),
            float(data.get("PITCH_KI", self._pitch_pid.ki)),
            float(data.get("PITCH_KD", self._pitch_pid.kd)),
        )

    @staticmethod
    def _roll_pitch_from_accel(
        ax: float, ay: float, az: float
    ) -> tuple[float, float]:
        """Estimate roll and pitch (radians) from accelerometer."""
        roll  = math.atan2(ay, math.sqrt(ax * ax + az * az))
        pitch = math.atan2(-ax, az)
        return roll, pitch

    # ------------------------------------------------------------------
    # Main update
    # ------------------------------------------------------------------

    def update(self, now: float) -> None:
        # Reload PID gains from DB on a slow cadence
        if now - self._last_gains_reload >= _GAINS_RELOAD_INTERVAL:
            self._reload_gains()
            self._last_gains_reload = now

        # Read pilot inputs
        inputs = self._client.latest("inputs")
        if inputs is None:
            inputs = {}
        surge = inputs.get("SURGE", 0) / _INPUT_SCALE
        sway  = inputs.get("SWAY",  0) / _INPUT_SCALE
        yaw   = inputs.get("YAW",   0) / _INPUT_SCALE
        heave = inputs.get("HEAVE", 0) / _INPUT_SCALE

        # Read IMU and compute stabilisation corrections
        roll_corr = pitch_corr = 0.0
        try:
            imu = self._client.latest("imu")
        except Exception:
            imu = None
        if imu:
            roll_ang, pitch_ang = self._roll_pitch_from_accel(
                imu.get("ACCEL_X", 0.0),
                imu.get("ACCEL_Y", 0.0),
                imu.get("ACCEL_Z", 9.81),
            )
            roll_corr  = self._roll_pid.update(roll_ang,  now)
            pitch_corr = self._pitch_pid.update(pitch_ang, now)

        # Mix DOF commands into per-motor values
        motors = mix(surge, sway, yaw, heave, roll_corr, pitch_corr)

        # Post to outputs table
        self._client.post(
            "outputs",
            MOTOR1=motors[0], MOTOR2=motors[1],
            MOTOR3=motors[2], MOTOR4=motors[3],
            MOTOR5=motors[4], MOTOR6=motors[5],
            MOTOR7=motors[6], MOTOR8=motors[7],
            S1=0, S2=0, S3=0,
        )

    # ------------------------------------------------------------------
    # Run loop
    # ------------------------------------------------------------------

    def run(self) -> None:
        stop = False

        def _handle(signum, _frame):  # noqa: ANN001 ARG001
            nonlocal stop
            stop = True

        signal.signal(signal.SIGTERM, _handle)
        signal.signal(signal.SIGINT,  _handle)

        _log.info("movement controller started")
        while not stop:
            now = time.monotonic()
            try:
                self.update(now)
            except Exception:
                _log.exception("update failed")
            elapsed = time.monotonic() - now
            sleep_for = max(0.0, _RATE - elapsed)
            if sleep_for:
                time.sleep(sleep_for)
        _log.info("movement controller stopped")


def run() -> None:
    setup_logging("movement")
    MovementController().run()


if __name__ == "__main__":
    run()
