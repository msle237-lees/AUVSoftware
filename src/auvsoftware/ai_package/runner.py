"""
Training / evaluation / real-world runner for the AUV PPO agent.

All three modes read world state from the database and write actions to it —
the runner never talks to hardware or simulation directly.

Modes
-----
TRAIN      – episodic rollout collection + policy updates; saves checkpoints.
EVAL       – deterministic policy execution over N episodes; no weight updates.
REALWORLD  – continuous loop at the control rate; no episode resets.
"""
from __future__ import annotations

import logging
import signal
import time
from enum import Enum, auto
from pathlib import Path
from typing import Optional

from auvsoftware.ai_package.agent import PPOAgent
from auvsoftware.ai_package.environment import AUVEnvironment
from auvsoftware.ai_package.reward import DefaultReward, RewardFunction
from auvsoftware.quick_request import AUVClient

log = logging.getLogger(__name__)


class RunMode(Enum):
    TRAIN     = auto()
    EVAL      = auto()
    REALWORLD = auto()


class AUVRunner:
    """
    Orchestrates the PPO agent across training, evaluation, and real-world runs.

    Parameters
    ----------
    mode            : which execution mode to use
    model_path      : where to load/save the policy checkpoint
    client          : AUVClient instance (defaults to localhost:8000)
    reward_fn       : custom RewardFunction (defaults to DefaultReward)
    max_steps       : steps per episode (TRAIN / EVAL only)
    step_delay      : seconds between steps — should match control rate (0.05 s = 20 Hz)
    total_timesteps : training budget (TRAIN only)
    save_every      : episodes between checkpoint saves (TRAIN only)
    n_eval_episodes : episodes to run in EVAL mode
    **agent_kwargs  : forwarded to PPOAgent constructor
    """

    def __init__(
        self,
        mode: RunMode = RunMode.TRAIN,
        model_path: Optional[str | Path] = None,
        client: Optional[AUVClient] = None,
        reward_fn: Optional[RewardFunction] = None,
        max_steps: int = 500,
        step_delay: float = 0.05,
        total_timesteps: int = 100_000,
        save_every: int = 10,
        n_eval_episodes: int = 10,
        **agent_kwargs,
    ) -> None:
        self.mode            = mode
        self.model_path      = Path(model_path) if model_path else Path("auv_ppo.pt")
        self.total_timesteps = total_timesteps
        self.save_every      = save_every
        self.n_eval_episodes = n_eval_episodes

        self.env = AUVEnvironment(
            client=client,
            reward_fn=reward_fn or DefaultReward(),
            max_steps=max_steps,
            step_delay=step_delay,
        )
        self.agent = PPOAgent(
            state_dim=AUVEnvironment.state_dim,
            action_dim=AUVEnvironment.action_dim,
            **agent_kwargs,
        )

        if self.model_path.exists():
            self.agent.load(self.model_path)

    # ── public entry point ────────────────────────────────────────────────────

    def start(self) -> None:
        dispatch = {
            RunMode.TRAIN:     self._train,
            RunMode.EVAL:      self._evaluate,
            RunMode.REALWORLD: self._realworld,
        }
        dispatch[self.mode]()

    # ── training ──────────────────────────────────────────────────────────────

    def _train(self) -> None:
        log.info("training started | budget=%d steps", self.total_timesteps)
        stopper  = _StopSignal()
        timestep = 0
        episode  = 0

        while timestep < self.total_timesteps and not stopper:
            state     = self.env.reset()
            ep_reward = 0.0

            while not stopper:
                action = self.agent.select_action(state)
                next_state, reward, terminated, truncated, _ = self.env.step(action)
                done = terminated or truncated

                self.agent.store_transition(state, action, reward, done)
                ep_reward += reward
                timestep  += 1
                state = next_state

                if self.agent.buffer.is_full():
                    info = self.agent.update()
                    log.debug("ppo update | loss=%.4f", info.get("loss", 0.0))

                if done:
                    break

            episode += 1
            log.info(
                "episode %d | reward=%.2f | total_steps=%d",
                episode, ep_reward, timestep,
            )

            if episode % self.save_every == 0:
                self.agent.save(self.model_path)

        self.agent.save(self.model_path)
        log.info("training complete | model saved to %s", self.model_path)

    # ── evaluation ────────────────────────────────────────────────────────────

    def _evaluate(self) -> None:
        log.info("evaluation started | episodes=%d", self.n_eval_episodes)
        stopper = _StopSignal()
        rewards = []

        for ep in range(1, self.n_eval_episodes + 1):
            if stopper:
                break
            state     = self.env.reset()
            ep_reward = 0.0
            done      = False

            while not done and not stopper:
                action = self.agent.select_action(state, deterministic=True)
                state, reward, terminated, truncated, _ = self.env.step(action)
                ep_reward += reward
                done = terminated or truncated

            rewards.append(ep_reward)
            log.info("eval episode %d | reward=%.2f", ep, ep_reward)

        if rewards:
            log.info(
                "evaluation complete | mean=%.2f  min=%.2f  max=%.2f",
                sum(rewards) / len(rewards),
                min(rewards),
                max(rewards),
            )

    # ── real-world ────────────────────────────────────────────────────────────

    def _realworld(self) -> None:
        log.info("real-world run started (Ctrl-C to stop)")
        stopper = _StopSignal()
        state   = self.env.observation()

        while not stopper:
            t0     = time.monotonic()
            action = self.agent.select_action(state, deterministic=True)
            state, _, _, _, _ = self.env.step(action)
            elapsed = time.monotonic() - t0
            log.debug("step latency %.3f s", elapsed)

        log.info("real-world run stopped")


# ── helpers ───────────────────────────────────────────────────────────────────

def run() -> None:
    """Default entry point: real-world policy execution with a saved checkpoint."""
    AUVRunner(mode=RunMode.REALWORLD).start()


class _StopSignal:
    """Catches SIGINT / SIGTERM and exposes as a boolean."""

    def __init__(self) -> None:
        self._stop = False
        signal.signal(signal.SIGINT,  self._set)
        signal.signal(signal.SIGTERM, self._set)

    def _set(self, *_) -> None:
        self._stop = True
        log.info("stop signal received")

    def __bool__(self) -> bool:
        return self._stop
