from smbus2 import SMBus
import time


class temperature:
    def __init__(self, bus_number: int = 1, address: int = 0x60):
        self.bus_number = bus_number
        self.address = address
        self.bus = SMBus(bus_number)
        
    def run(self):
        pass # Implement temperature sensor logic here, such as reading temperature data and processing it for use in monitoring and control