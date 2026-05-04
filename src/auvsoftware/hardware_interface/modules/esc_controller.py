from auvsoftware.config import get_env
from auvsoftware.hardware_interface.i2c_commands import write

_BUS: int = int(get_env("I2C_BUS", required=True))
_ADDRESS: int = int(get_env("ESC_I2C_ADDRESS", required=True), 16)

_REGISTER: int = 0x00
_MIN: int = 0
_MAX: int = 255


def _clamp(value: int) -> int:
    return max(_MIN, min(_MAX, value))


def set_thrust(motor1: int, motor2: int, motor3: int, motor4: int, vertical: int) -> None:
    """Send thrust values (0-255) to all motors via Pico over I2C."""
    thrusts = [_clamp(v) for v in (motor1, motor2, motor3, motor4, vertical)]
    payload = bytes([_REGISTER] + thrusts)
    write(_BUS, _ADDRESS, payload)
