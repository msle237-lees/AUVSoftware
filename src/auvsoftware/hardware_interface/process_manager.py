import multiprocessing
import time
from typing import Callable

from auvsoftware.config import get_env
from auvsoftware.hardware_interface.scanner import scan_i2c_bus

_RETRY_DELAY: float = 5.0


def _with_retry(name: str, fn: Callable) -> None:
    """Run *fn* in a loop, restarting after any exception (e.g. DB not yet up)."""
    while True:
        try:
            fn()
        except KeyboardInterrupt:
            break
        except Exception as exc:
            print(f"[{name}] crashed: {exc!r} — retrying in {_RETRY_DELAY}s")
            time.sleep(_RETRY_DELAY)


def _run_esc() -> None:
    from auvsoftware.hardware_interface.modules.esc_controller import ESCController
    _with_retry("esc", ESCController().run)


def _run_arm() -> None:
    from auvsoftware.hardware_interface.modules.arm_controller import ArmController
    _with_retry("arm", ArmController().run)


def _run_imu() -> None:
    from auvsoftware.hardware_interface.modules.imu_controller import ImuController
    _with_retry("imu", ImuController().run)


def _run_psa() -> None:
    from auvsoftware.hardware_interface.modules.psa_controller import PsaController
    _with_retry("psa", PsaController().run)


def _run_torpedo() -> None:
    from auvsoftware.hardware_interface.modules.tor_controller import TorpedoController
    _with_retry("torpedo", TorpedoController().run)


def _run_pressure() -> None:
    from auvsoftware.hardware_interface.modules.pre_controller import PressureController
    _with_retry("pressure", PressureController().run)


def _run_display() -> None:
    from auvsoftware.hardware_interface.modules.dis_controller import DisplayController
    _with_retry("display", DisplayController().run)


# (flag_env_key, address_env_key, short_name, target_fn)
_REGISTRY: list[tuple[str, str, str, Callable]] = [
    ("ESC_CONTROLLER",      "ESC_ADDRESS",      "esc",      _run_esc),
    ("ARM_CONTROLLER",      "ARM_ADDRESS",      "arm",      _run_arm),
    ("IMU_CONTROLLER",      "IMU_ADDRESS",      "imu",      _run_imu),
    ("PSA_CONTROLLER",      "PSA_ADDRESS",      "psa",      _run_psa),
    ("TORPEDO_CONTROLLER",  "TORPEDO_ADDRESS",  "torpedo",  _run_torpedo),
    ("PRESSURE_CONTROLLER", "PRESSURE_ADDRESS", "pressure", _run_pressure),
    ("DISPLAY_CONTROLLER",  "DISPLAY_ADDRESS",  "display",  _run_display),
]

_NAME_TO_TARGET: dict[str, Callable] = {name: fn for _, _, name, fn in _REGISTRY}


class HardwareProcessManager:
    def __init__(self, dry_run: bool = False) -> None:
        """
        Args:
            dry_run: When True, log what would happen instead of spawning real
                     processes. Useful for testing detection + flag logic without
                     live hardware or a DB.
        """
        self.dry_run = dry_run
        self._processes: dict[str, multiprocessing.Process] = {}

    def reconcile(self) -> None:
        """
        Scan the I2C bus and sync running processes against .env config.
        Starts a controller only when its flag is True AND its device is detected.
        Stops a controller when either condition becomes false.
        """
        bus = int(get_env("I2C_BUS_NUMBER", required=True))
        detected = set(scan_i2c_bus(bus))

        for flag_key, addr_key, name, _ in _REGISTRY:
            raw = get_env(flag_key, default="False").strip().lower()
            enabled = raw in ("true", "1", "yes")
            addr_str = get_env(addr_key, default="")
            address = int(addr_str.strip(), 16) if addr_str.strip() else None

            should_run = enabled and address is not None and address in detected
            is_running = name in self._processes and self._processes[name].is_alive()

            if should_run and not is_running:
                self._spawn(name)
            elif not should_run and is_running:
                self.stop(name)

    def start_all(self) -> None:
        """Start all .env-enabled controllers regardless of I2C detection."""
        for flag_key, _, name, _ in _REGISTRY:
            raw = get_env(flag_key, default="False").strip().lower()
            if raw in ("true", "1", "yes"):
                self._spawn(name)

    def stop_all(self) -> None:
        """Terminate all running controller processes."""
        for name in list(self._processes):
            self.stop(name)

    def start(self, name: str) -> None:
        """Manually start a controller by short name (e.g. 'esc')."""
        if name not in _NAME_TO_TARGET:
            valid = sorted(_NAME_TO_TARGET)
            raise ValueError(f"Unknown controller: '{name}'. Valid: {valid}")
        self._spawn(name)

    def stop(self, name: str) -> None:
        """Terminate a controller by short name. No-op if not running."""
        if self.dry_run:
            print(f"[dry_run] stop: {name}")
            return
        p = self._processes.pop(name, None)
        if p is None:
            return
        p.terminate()
        p.join(timeout=5)
        if p.is_alive():
            p.kill()

    def status(self) -> dict[str, dict]:
        """
        Return status for every registered controller.

        Each entry: {"enabled": bool, "detected": bool, "running": bool,
        "pid": int|None}
        """
        try:
            bus = int(get_env("I2C_BUS_NUMBER", default="1"))
            detected = set(scan_i2c_bus(bus))
        except OSError:
            detected = set()

        result: dict[str, dict] = {}
        for flag_key, addr_key, name, _ in _REGISTRY:
            p = self._processes.get(name)
            alive = p is not None and p.is_alive()
            addr_str = get_env(addr_key, default="")
            address = int(addr_str.strip(), 16) if addr_str.strip() else None
            result[name] = {
                "enabled": get_env(flag_key, default="False").strip().lower()
                in ("true", "1", "yes"),
                "detected": address is not None and address in detected,
                "running": alive,
                "pid": p.pid if alive else None,
            }
        return result

    def _spawn(self, name: str) -> None:
        if self.dry_run:
            print(f"[dry_run] spawn: {name}")
            return
        if name in self._processes and self._processes[name].is_alive():
            return
        p = multiprocessing.Process(
            target=_NAME_TO_TARGET[name], name=name, daemon=True
        )
        p.start()
        self._processes[name] = p
