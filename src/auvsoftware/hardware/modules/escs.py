from smbus2 import SMBus
import threading
import time


class escs:
    def __init__(self, bus_number: int, address: int, bus_lock: threading.Lock) -> None:
        self.bus_number = bus_number
        self.address = address
        self.bus = SMBus(bus_number)
        
    def run(self, stop_event : threading.Event) -> None:
        pass  # Implement arm control logic here, such as sending position commands and reading feedback