import functools
import multiprocessing
from pathlib import Path

from auvsoftware.config import get_env

_DB_DIR = Path(__file__).parent / "db_manager"

# Extend this list as high-level packages are implemented.
_SERVICES: list[str] = ["db", "hardware_interface", "movement", "camera", "ai"]


def _run_db() -> None:
    """
    Start the FastAPI DB server.

    Inserts the db_manager directory into sys.path so its bare local
    imports (routers, deps, config) resolve without changing those files.
    """
    import logging
    import sys

    import uvicorn

    from auvsoftware.logging_config import setup_logging
    setup_logging("db")
    log = logging.getLogger(__name__)

    sys.path.insert(0, str(_DB_DIR))

    try:
        from run import app  # noqa: PLC0415
    except Exception:
        log.exception("DB app failed to import")
        return

    host = get_env("AUV_HOST", default="0.0.0.0")
    port = int(get_env("AUV_PORT", default="8000"))
    try:
        uvicorn.run(app, host=host, port=port, reload=False, log_config=None)
    except BaseException:
        log.exception("DB server crashed")
        raise


def _run_hardware_interface(simulation: bool = False) -> None:
    """Start the hardware interface (real or simulated)."""
    from auvsoftware.logging_config import setup_logging
    setup_logging("hardware_interface")
    from auvsoftware.hardware_interface.hardware_interface import run
    run(simulation=simulation)


def _run_movement() -> None:
    """Start the movement controller."""
    from auvsoftware.logging_config import setup_logging
    setup_logging("movement")
    from auvsoftware.movement_package.movement import run
    run()


def _run_camera() -> None:
    """Start the camera package (streaming server + detection)."""
    from auvsoftware.logging_config import setup_logging
    setup_logging("camera")
    from auvsoftware.camera_package.camera_manager import run
    run()


def _run_ai() -> None:
    """Start the AI runner (real-world policy execution by default)."""
    from auvsoftware.logging_config import setup_logging
    setup_logging("ai")
    from auvsoftware.ai_package.runner import run
    run()


_TARGETS: dict[str, object] = {
    "db": _run_db,
    "hardware_interface": _run_hardware_interface,
    "movement": _run_movement,
    "camera": _run_camera,
    "ai": _run_ai,
}


class ProcessManager:
    def __init__(self, dry_run: bool = False) -> None:
        """
        Args:
            dry_run: When True, log actions without starting real processes.
                     Useful for testing without live hardware or a DB.
        """
        self.dry_run = dry_run
        self._processes: dict[str, multiprocessing.Process] = {}

    def start_all(self) -> None:
        """Start all registered services."""
        for name in _SERVICES:
            self.start(name)

    def stop_all(self) -> None:
        """Terminate all running services."""
        for name in list(self._processes):
            self.stop(name)

    def start(self, name: str, *, simulation: bool = False) -> None:
        """Start a service by name. No-op if already running.

        The ``simulation`` flag is forwarded to ``hardware_interface`` only.
        """
        if name not in _TARGETS:
            raise ValueError(
                f"Unknown service: '{name}'. Valid: {_SERVICES}"
            )
        if self._is_alive(name):
            return
        if self.dry_run:
            sim_tag = " [sim]" if simulation and name == "hardware_interface" else ""
            print(f"[dry_run] start: {name}{sim_tag}")
            return
        if name == "hardware_interface":
            target = functools.partial(_run_hardware_interface, simulation=simulation)
        else:
            target = _TARGETS[name]
        p = multiprocessing.Process(target=target, name=name, daemon=True)
        p.start()
        self._processes[name] = p

    def stop(self, name: str) -> None:
        """Terminate a service. No-op if not running."""
        if self.dry_run:
            print(f"[dry_run] stop: {name}")
            return
        proc = self._processes.pop(name, None)
        if proc is None:
            return
        proc.terminate()
        proc.join(timeout=5)
        if proc.is_alive():
            proc.kill()

    def status(self) -> dict[str, dict]:
        """Return running status for every registered service."""
        result: dict[str, dict] = {}
        for name in _SERVICES:
            alive = self._is_alive(name)
            proc = self._processes.get(name)
            result[name] = {
                "running": alive,
                "pid": proc.pid if alive else None,
            }
        return result

    def _is_alive(self, name: str) -> bool:
        proc = self._processes.get(name)
        return proc is not None and proc.is_alive()
