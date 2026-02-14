import os
import time
from typing import Any, Dict, Optional

import pygame
import requests


class Controller:
    def __init__(self):
        pygame.init()
        self.joystick = None
        self._initialize_joystick()

        # --- API/DB posting config ---
        self.api_base_url: str = os.getenv("API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
        self.runs_endpoint: str = os.getenv("RUNS_ENDPOINT", "/runs")
        self.control_inputs_endpoint: str = os.getenv("CONTROL_INPUTS_ENDPOINT", "/inputs")

        # Request behavior
        self.http_timeout_s: float = float(os.getenv("API_TIMEOUT_S", "3.0"))
        self.min_post_interval_s: float = float(os.getenv("MIN_POST_INTERVAL_S", "0.05"))  # 20 Hz default
        self._last_post_t: float = 0.0

        # Run + sequencing
        self.run_id: Optional[int] = 1
        self.seq: int = 0

        # Reuse a session for performance
        self._session = requests.Session()

    def _initialize_joystick(self):
        if pygame.joystick.get_count() > 0:
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()
            print(f"Joystick initialized: {self.joystick.get_name()}")
        else:
            print("No joystick detected. Please connect a joystick and restart the application.")

    def map(self, x: float) -> int:
        """
        Map value from [-1.0, 1.0] to [0, 255].

        @param x Raw axis value in [-1.0, 1.0].
        @return Mapped integer in [0, 255].
        """
        return int((x - (-1)) * (255 - 0) / (1 - (-1)) + 0)

    def get_input(self) -> Optional[Dict[str, Any]]:
        """
        Read joystick state snapshot.

        @return Dict with keys 'axes', 'buttons', 'hats' or None if joystick not available.
        """
        if not self.joystick:
            return None

        pygame.event.pump()  # Process event queue

        axes = [self.map(self.joystick.get_axis(i)) for i in range(self.joystick.get_numaxes())]
        buttons = [self.joystick.get_button(i) for i in range(self.joystick.get_numbuttons())]
        hats = [self.joystick.get_hat(i) for i in range(self.joystick.get_numhats())]

        return {"axes": axes, "buttons": buttons, "hats": hats}

    def _now_us(self) -> int:
        """
        Get current time in microseconds.

        @return Microseconds since epoch.
        """
        return int(time.time() * 1_000_000)

    def _ensure_run_id(self) -> bool:
        """
        Ensure we have a run_id by creating a run if needed.

        This assumes your API supports POST {API_BASE_URL}{RUNS_ENDPOINT} and returns JSON with an 'id' field.

        @return True if run_id is available, False otherwise.
        """
        if self.run_id is not None:
            return True

        url = f"{self.api_base_url}{self.runs_endpoint}"
        try:
            # If your RunCreate requires fields, add them here
            resp = self._session.post(url, json={}, timeout=self.http_timeout_s)
            resp.raise_for_status()
            data = resp.json()
            rid = data.get("id")
            if rid is None:
                print(f"[WARN] Run create response missing 'id': {data}")
                return False
            self.run_id = int(rid)
            print(f"[INFO] Created run_id={self.run_id}")
            return True
        except requests.RequestException as e:
            print(f"[WARN] Failed to create run: {e}")
            return False

    def updateDB(self, data: Dict[str, Any]) -> None:
        """
        Post one control sample to the database through your FastAPI API.

        Expected payload keys (your mapped control set):
            x, y, z, yaw, s1, s2, s3

        This method will:
        - lazily create a run (POST /runs) if self.run_id is not set
        - add t_us + seq + run_id
        - POST to CONTROL_INPUTS_ENDPOINT

        Environment variables:
            API_BASE_URL (default: http://127.0.0.1:8000)
            RUNS_ENDPOINT (default: /runs)
            CONTROL_INPUTS_ENDPOINT (default: /control-inputs)
            API_TIMEOUT_S (default: 3.0)
            MIN_POST_INTERVAL_S (default: 0.05)

        @param data Dict containing control fields to post.
        """
        # Simple rate limit to avoid spamming the API
        now = time.time()
        if (now - self._last_post_t) < self.min_post_interval_s:
            return

        if not self._ensure_run_id():
            return

        self.seq += 1

        payload = {
            "run_id": self.run_id,
            "t_us": self._now_us(),
            "seq": self.seq,
            "x": float(data.get("x", 0.0)),
            "y": float(data.get("y", 0.0)),
            "z": float(data.get("z", 0.0)),
            "yaw": float(data.get("yaw", 0.0)),
            "s1": int(data.get("s1", 0)),
            "s2": int(data.get("s2", 0)),
            "s3": int(data.get("s3", 0)),
        }

        url = f"{self.api_base_url}{self.control_inputs_endpoint}"

        try:
            resp = self._session.post(url, json=payload, timeout=self.http_timeout_s)
            resp.raise_for_status()
            self._last_post_t = now
        except requests.HTTPError as e:
            # If the run was deleted/reset server-side, clear run_id and try to recreate next time
            print(f"[WARN] POST failed ({resp.status_code if 'resp' in locals() else 'n/a'}): {e}")
        except requests.RequestException as e:
            print(f"[WARN] Failed to post control input: {e}")

    def process(self):
        input_data = self.get_input()
        if input_data:
            X = input_data["axes"][0]  # Left stick horizontal
            Y = input_data["axes"][1]  # Left stick vertical
            Z = input_data["axes"][4]  # Right stick vertical
            R = input_data["axes"][3]  # Right stick horizontal

            S1 = input_data["buttons"][4]  # Button A
            S2 = input_data["buttons"][5]  # Button B
            S3 = input_data["buttons"][0]  # Button X

            # print(f"Processed Input - X: {X}, Y: {Y}, Z: {Z}, R: {R}, S1: {S1}, S2: {S2}, S3: {S3}")

            # Post to DB/API
            self.updateDB(
                {
                    "x": X,
                    "y": Y,
                    "z": Z,
                    "yaw": R,  # R = Yaw
                    "s1": S1,
                    "s2": S2,
                    "s3": S3,
                }
            )

def run_controller():
    controller = Controller()
    while True:
        controller.process()

if __name__ == "__main__":
    controller = Controller()
    while True:
        controller.process()