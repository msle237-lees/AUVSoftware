"""
src/auvsoftware/movement/main.py

Handles translation of input commands to movement commands.
Input data format:
    input_data = {
        "X" : 0.00,
        "Y" : 0.00,
        "Z" : 0.00,
        "Roll" : 0.00,
        "Pitch" : 0.00,
        "Yaw" : 0.00,
        "S1" : 0.00,
        "S2" : 0.00,
        "S3" : 0.00
    }
"""

from __future__ import annotations

from auvsoftware.database.crud import get_latest_inputs, insert_motor, insert_servo


class Movement:
    def __init__(self, config_path: str):
        self.config_path = config_path
