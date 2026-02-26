from smbus2 import SMBus
import time


class arm:
    def __init__(self, bus_number: int = 1, address: int = 0x50):
        self.bus_number = bus_number
        self.address = address
        self.bus = SMBus(bus_number)
        
    def run(self):
        pass  # Implement arm control logic here, such as sending position commands and reading feedback