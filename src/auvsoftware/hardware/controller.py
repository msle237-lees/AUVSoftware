from __future__ import annotations

from dataclasses import dataclass, field
from importlib import import_module
from smbus2 import SMBus
import threading
import time
from typing import Callable, Dict, Optional, Set, Protocol, runtime_checkable


@runtime_checkable
class Runnable(Protocol):
    """@brief Contract for hardware modules runnable by the Controller."""
    def run(self, stop_event: threading.Event) -> None:
        ...


@dataclass
class DeviceSpec:
    """
    @brief Declares how an I2C device maps to a runnable module.

    @param name Human-friendly name for logs and control.
    @param address I2C address (7-bit).
    @param module_path Python import path for the module file.
    @param class_name Class name inside the module to instantiate.
    @param enabled Whether the controller is allowed to run this module.
    """
    name: str
    address: int
    module_path: str
    class_name: str
    enabled: bool = True

    # Runtime state
    present: bool = False
    thread: Optional[threading.Thread] = None
    stop_event: threading.Event = field(default_factory=threading.Event)


class Controller:
    """
    @brief Central controller for dynamic I2C device management in the AUV system.

    @details
    The Controller class is responsible for monitoring the I2C bus for
    connected devices and managing their lifecycle within the AUV software
    stack. It continuously scans the bus for address changes and detects
    when new device addresses appear or disappear.

    When a recognized I2C address is detected, the Controller:
        - Maps the address to a known electrical board definition stored
          in an internal dictionary.
        - Instantiates the corresponding module interface.
        - Launches a dedicated thread to handle communication with that module.
    
    Each module thread operates independently, allowing concurrent
    interaction with multiple hardware subsystems (e.g., IMU, depth sensor,
    power monitor, motor controller).

    The Controller also provides configuration-level control over which
    modules are enabled or disabled. This allows:
        - Selective activation of hardware subsystems.
        - Development-time testing without specific boards connected.
        - Runtime flexibility for mission-specific configurations.

    @note
    This class is designed for asynchronous, non-blocking hardware
    integration in embedded or companion-computer AUV architectures.

    @warning
    Proper thread synchronization and bus access protection mechanisms
    should be implemented to prevent I2C contention or race conditions.
    """

    def __init__(self, bus_number: int = 1) -> None:
        self.bus_number = bus_number
        self.bus_lock = threading.Lock()

        # Declarative registry: add new boards by adding one line here.
        self.devices: Dict[str, DeviceSpec] = {
            "arm": DeviceSpec(
                name="Manipulator Arm",
                address=0x50,
                module_path="hardware.modules.arm",
                class_name="arm",
                enabled=True,
            ),
            "battery": DeviceSpec(
                name="Battery Monitor",
                address=0x30,
                module_path="hardware.modules.battery",
                class_name="battery",
                enabled=True,
            ),
            "depth": DeviceSpec(
                name="Depth Sensor",
                address=0x20,
                module_path="hardware.modules.depth",
                class_name="depth",
                enabled=True,
            ),
            "escs": DeviceSpec(
                name="Motor Controller",
                address=0x40,
                module_path="hardware.modules.escs",
                class_name="escs",
                enabled=True,
            ),
            "imu": DeviceSpec(
                name="IMU",
                address=0x10,
                module_path="hardware.modules.imu",
                class_name="imu",
                enabled=True,
            ),
            "temperature": DeviceSpec(
                name="Temperature Sensor",
                address=0x60,
                module_path="hardware.modules.temperature",
                class_name="temperature",
                enabled=True,
            ),
            "torpedoes": DeviceSpec(
                name="Torpedo Controller",
                address=0x70,
                module_path="hardware.modules.torpedoes",
                class_name="torpedoes",
                enabled=True,
            ),
        }

        # Cache for last seen bus scan result
        self._last_seen_addresses: Set[int] = set()

    def enable_module(self, key: str, enabled: bool) -> None:
        """
        @brief Enable or disable a module by registry key.

        @details
        Disabling a module will stop it if it is running, even if the device
        remains present on the I2C bus.

        @param key Registry key (e.g., "imu", "depth").
        @param enabled True to allow running, False to prevent running.
        """
        if key not in self.devices:
            raise KeyError(f"Unknown module key: {key}")

        spec = self.devices[key]
        spec.enabled = enabled

        if not enabled:
            self._stop_device(spec)

    def scan_i2c_addresses(self) -> Set[int]:
        """
        @brief Scan the I2C bus and return detected 7-bit addresses.

        @details
        Attempts a read to each address (0x03..0x77). Addresses that respond
        are included in the returned set.

        @return Set of detected device addresses.
        """
        found: Set[int] = set()

        with SMBus(self.bus_number) as bus:
            for addr in range(0x03, 0x78):
                try:
                    bus.read_byte(addr)
                    found.add(addr)
                except OSError:
                    continue

        return found

    def _load_module_factory(self, spec: DeviceSpec) -> Callable[[], Runnable]:
        """
        @brief Dynamically import and return a factory that constructs the module instance.

        @param spec Device specification describing module import + class.
        @return Callable that creates an instance of the module class.
        """
        mod = import_module(spec.module_path)
        cls = getattr(mod, spec.class_name)
        return lambda: cls(bus_number=self.bus_number, address=spec.address, bus_lock=self.bus_lock)

    def _start_device(self, spec: DeviceSpec) -> None:
        """
        @brief Start the module thread for a device if not already running.

        @param spec Device specification.
        """
        if spec.thread is not None and spec.thread.is_alive():
            return

        spec.stop_event.clear()

        def _runner() -> None:
            factory = self._load_module_factory(spec)
            module = factory()

            # Expect module.run(stop_event) for cooperative cancellation.
            # If your module signature differs, adjust here once, not everywhere.
            module.run(spec.stop_event)

        spec.thread = threading.Thread(target=_runner, name=f"mod:{spec.name}", daemon=True)
        spec.thread.start()

    def _stop_device(self, spec: DeviceSpec) -> None:
        """
        @brief Signal a module thread to stop and clear runtime state.

        @param spec Device specification.
        """
        spec.stop_event.set()

        # Optional: join briefly so the thread can exit cleanly.
        if spec.thread is not None and spec.thread.is_alive():
            spec.thread.join(timeout=1.0)

        spec.thread = None
        spec.present = False

    def reconcile(self, detected_addresses: Set[int]) -> None:
        """
        @brief Reconcile detected bus addresses with registry and start/stop modules.

        @details
        - If a device appears and is enabled: start its module thread.
        - If a device disappears: stop its module thread.
        - If a device is present but disabled: ensure stopped.

        @param detected_addresses Set of addresses detected in the latest scan.
        """
        for spec in self.devices.values():
            now_present = spec.address in detected_addresses

            # Device appeared
            if now_present and not spec.present:
                spec.present = True
                if spec.enabled:
                    self._start_device(spec)

            # Device disappeared
            elif not now_present and spec.present:
                self._stop_device(spec)

            # Device present but disabled
            elif now_present and spec.present and not spec.enabled:
                self._stop_device(spec)

    def monitor_bus(self, scan_interval: float = 2.0) -> None:
        """
        @brief Continuously monitor I2C bus for device changes.

        @param scan_interval Seconds between scans.
        """
        while True:
            detected = self.scan_i2c_addresses()

            # Only reconcile when something changed to reduce churn/logging.
            if detected != self._last_seen_addresses:
                self.reconcile(detected)
                self._last_seen_addresses = detected

            time.sleep(scan_interval)
            
    def run(self) -> None:
        """
        @brief Start the controller's bus monitoring loop.

        @details
        This method blocks indefinitely. It should be run in a dedicated thread
        or as the main entry point of the hardware management process.
        """
        self.monitor_bus()
        
if __name__ == "__main__":
    controller = Controller(bus_number=1)
    controller.run()