"""
Reward functions for the AUV RL environment.

Subclass RewardFunction and pass an instance to AUVEnvironment or AUVRunner
to customise the learning objective.
"""
from __future__ import annotations

import math
from typing import Optional

from auvsoftware.ai_package.environment import WorldState


class RewardFunction:
    """Base class. Implement compute() for custom rewards."""

    def reset(self) -> None:
        """Called at the start of every episode."""

    def compute(self, state: WorldState, prev: Optional[WorldState]) -> float:
        raise NotImplementedError


class StabilityReward(RewardFunction):
    """
    Rewards minimising roll and pitch (tilt from gravity vector).
    Penalises rotational angular rates.
    """

    def reset(self) -> None:
        pass

    def compute(self, state: WorldState, prev: Optional[WorldState]) -> float:
        roll  = math.atan2(
            state.accel_y,
            math.sqrt(state.accel_x ** 2 + state.accel_z ** 2),
        )
        pitch = math.atan2(-state.accel_x, state.accel_z)
        tilt_penalty = -(abs(roll) + abs(pitch))

        spin_penalty = -(
            abs(state.gyro_x) + abs(state.gyro_y) + abs(state.gyro_z)
        ) * 0.1

        return tilt_penalty + spin_penalty


class DepthReward(RewardFunction):
    """Rewards maintaining a target depth."""

    def __init__(self, target_depth: float = 1.0) -> None:
        self.target_depth = target_depth

    def reset(self) -> None:
        pass

    def compute(self, state: WorldState, prev: Optional[WorldState]) -> float:
        return -abs(state.depth - self.target_depth)


class CompositeReward(RewardFunction):
    """Linearly combine multiple reward functions with optional weights."""

    def __init__(self, components: list[tuple[RewardFunction, float]]) -> None:
        self._components = components

    def reset(self) -> None:
        for fn, _ in self._components:
            fn.reset()

    def compute(self, state: WorldState, prev: Optional[WorldState]) -> float:
        return sum(w * fn.compute(state, prev) for fn, w in self._components)


class DefaultReward(CompositeReward):
    """
    Stability (1.0) + depth tracking to 1 m (1.0).
    Override target_depth for a different setpoint.
    """

    def __init__(self, target_depth: float = 1.0) -> None:
        super().__init__([
            (StabilityReward(), 1.0),
            (DepthReward(target_depth), 1.0),
        ])
