import time


class PIDController:
    """
    Discrete PID with derivative-on-measurement and integral anti-windup.

    Derivative is computed on the measurement (not the error) to avoid a
    spike when the setpoint changes suddenly.  Anti-windup clamps the
    accumulated integral to the output range divided by ki.
    """

    def __init__(
        self,
        kp: float,
        ki: float,
        kd: float,
        setpoint: float = 0.0,
        output_limits: tuple[float, float] = (-1.0, 1.0),
    ) -> None:
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.setpoint = setpoint
        self.output_limits = output_limits
        self._integral: float = 0.0
        self._prev_measurement: float = 0.0
        self._prev_time: float | None = None

    def update(self, measurement: float, now: float | None = None) -> float:
        if now is None:
            now = time.monotonic()

        dt = (now - self._prev_time) if self._prev_time is not None else 0.0
        self._prev_time = now

        error = self.setpoint - measurement

        if dt > 0.0:
            self._integral += error * dt
            # Anti-windup: keep integral within a range that can't exceed output limits
            lo, hi = self.output_limits
            if self.ki != 0.0:
                max_i = abs(hi / self.ki)
                self._integral = max(-max_i, min(max_i, self._integral))
            derivative = -(measurement - self._prev_measurement) / dt
        else:
            derivative = 0.0

        self._prev_measurement = measurement

        output = self.kp * error + self.ki * self._integral + self.kd * derivative
        lo, hi = self.output_limits
        return max(lo, min(hi, output))

    def reset(self) -> None:
        self._integral = 0.0
        self._prev_measurement = 0.0
        self._prev_time = None

    def set_gains(self, kp: float, ki: float, kd: float) -> None:
        """Update gains and reset internal state only when they change."""
        if (kp, ki, kd) != (self.kp, self.ki, self.kd):
            self.kp, self.ki, self.kd = kp, ki, kd
            self.reset()
