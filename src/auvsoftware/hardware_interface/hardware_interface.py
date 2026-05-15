import argparse
import logging
import signal
import time

from auvsoftware.logging_config import setup_logging

_RECONCILE_INTERVAL: float = 5.0
_log = logging.getLogger(__name__)


def run(simulation: bool = False) -> None:
    """Start the hardware interface — real or simulated."""
    setup_logging("hardware_interface")

    stop = False

    def _handle_signal(signum, _frame):  # noqa: ANN001 ARG001
        nonlocal stop
        _log.info("hardware_interface received signal %s — shutting down", signum)
        stop = True

    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)

    if simulation:
        _log.info("hardware_interface starting in simulation mode")
        from auvsoftware.hardware_interface.simulation import SimulationController
        SimulationController().run()
        return

    from auvsoftware.hardware_interface.process_manager import HardwareProcessManager
    pm = HardwareProcessManager()

    _log.info("hardware_interface started")
    try:
        while not stop:
            try:
                pm.reconcile()
            except Exception:
                _log.exception("reconcile failed")
            time.sleep(_RECONCILE_INTERVAL)
    finally:
        pm.stop_all()
        _log.info("hardware_interface stopped")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AUV hardware interface")
    parser.add_argument(
        "--simulation", "-s",
        action="store_true",
        help="Run against the HoloOcean simulator instead of real hardware",
    )
    args = parser.parse_args()
    run(simulation=args.simulation)
