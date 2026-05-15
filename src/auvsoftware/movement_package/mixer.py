"""
Thrust allocation for an 8-thruster AUV.

Physical layout (top view, x = starboard/right, y = forward):

    All dimensions measured from centre of mass (COM), mm.

    Horizontal thrusters (M1-M4), 45° outward-mounted:

             y = +360 (fore)
    M1(-227.5,+360)      M2(+227.5,+360)
        ↖   ◄─── 455 ───►   ↗
                 COM
        ↙                   ↘
    M4(-227.5,-360)      M3(+227.5,-360)
             y = -360 (aft)
    x = -227.5 (port)    x = +227.5 (stbd)

    Vertical thrusters (M5-M8), positive command = push DOWN:
    M5(-227.5,+162.5)    M6(+227.5,+162.5)   ← y = +162.5
    M8(-227.5,-162.5)    M7(+227.5,-162.5)   ← y = -162.5

    Bearing angles to thruster position (CCW from +x, for reference):
        Corner thrusters: atan2(360, 227.5) = 57.7°
            M1 → 122.3° (=180°−57.7°)   M2 →  57.7°
            M3 → 237.7° (=180°+57.7°)   M4 → 302.3° (=360°−57.7°)
        Side verticals: atan2(162.5, 227.5) = 35.5°
            M5 → 144.5°   M6 →  35.5°
            M7 → 324.5°   M8 → 215.5°

    Horizontal mount angles (45° from vehicle axes):
        M1 (port-fore)  faces NE ( 45°): surge+  sway+  yaw+
        M2 (stbd-fore)  faces NW (135°): surge+  sway−  yaw−
        M3 (stbd-aft)   faces SW (225°): surge−  sway−  yaw+
        M4 (port-aft)   faces SE (315°): surge−  sway+  yaw−

    Yaw sign: positive = clockwise viewed from above (stbd turn).
    Verified by τ_cw = Σ(yi·Fxi − xi·Fyi) for each motor.

    Vertical thrusters (M5-M8), positive command = push DOWN:
        M5 (port-fore):  heave+  roll−  pitch−
        M6 (stbd-fore):  heave+  roll+  pitch−
        M7 (stbd-aft):   heave+  roll+  pitch+
        M8 (port-aft):   heave+  roll−  pitch+

    PID correction conventions:
        roll_corr  > 0 → raises stbd side  (M6/M7 push down, M5/M8 ease)
        pitch_corr > 0 → raises aft / pushes nose down
                         (M7/M8 push down, M5/M6 ease)
    Because the PID output is negative when angle > 0, the mixed
    result produces the correct restoring force automatically.
"""

import numpy as np

_NEUTRAL = 127
_MAX_DELTA = 127

# rows = motors [M1..M4], cols = [surge, sway, yaw]
_H_MATRIX = np.array(
    [
        [+1.0, +1.0, +1.0],  # M1 port-fore — NE face (45°)
        [+1.0, -1.0, -1.0],  # M2 stbd-fore — NW face (135°)
        [-1.0, -1.0, +1.0],  # M3 stbd-aft  — SW face (225°)
        [-1.0, +1.0, -1.0],  # M4 port-aft  — SE face (315°)
    ],
    dtype=float,
)

# rows = motors [M5..M8], cols = [heave, roll_corr, pitch_corr]
_V_MATRIX = np.array(
    [
        [+1.0, -1.0, -1.0],  # M5 FL_V
        [+1.0, +1.0, -1.0],  # M6 FR_V
        [+1.0, +1.0, +1.0],  # M7 RR_V
        [+1.0, -1.0, +1.0],  # M8 RL_V
    ],
    dtype=float,
)


def _normalize(values: np.ndarray) -> np.ndarray:
    """Scale down uniformly if any element exceeds [-1, 1]."""
    max_mag = float(np.abs(values).max())
    return values / max_mag if max_mag > 1.0 else values


def mix(
    surge: float,
    sway: float,
    yaw: float,
    heave: float,
    roll_corr: float,
    pitch_corr: float,
) -> list[int]:
    """
    Combine normalised DOF commands into 8 motor values (0-255, 127=neutral).

    All inputs must be in [-1, 1].  Returns [M1, M2, M3, M4, M5, M6, M7, M8].
    """
    h = _normalize(_H_MATRIX @ np.array([surge, sway, yaw], dtype=float))
    v = _normalize(_V_MATRIX @ np.array([heave, roll_corr, pitch_corr], dtype=float))

    raw = np.concatenate([h, v])
    return [int(np.clip(_NEUTRAL + r * _MAX_DELTA, 0, 255)) for r in raw]
