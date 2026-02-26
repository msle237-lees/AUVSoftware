from smbus2 import SMBus
import time


class escs:
    def __init__(self, bus_number: int = 1, address: int = 0x40):
        self.bus_number = bus_number
        self.address = address
        self.bus = SMBus(bus_number)
        
    def run(self):
        pass  # Implement ESC control logic here, such as sending speed commands and reading status