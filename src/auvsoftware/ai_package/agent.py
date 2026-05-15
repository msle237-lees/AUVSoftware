"""
PPO (Proximal Policy Optimisation) agent.

Requires PyTorch, which ships as a transitive dependency of ultralytics.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import numpy as np

log = logging.getLogger(__name__)

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    _TORCH = True
except ImportError:
    _TORCH = False
    log.warning("torch not available – PPOAgent disabled")


# ── Network ───────────────────────────────────────────────────────────────────

if _TORCH:
    class _MLP(nn.Module):
        def __init__(
            self,
            in_dim: int,
            out_dim: int,
            hidden: tuple[int, ...] = (256, 256),
        ) -> None:
            super().__init__()
            layers: list[nn.Module] = []
            prev = in_dim
            for h in hidden:
                layers += [nn.Linear(prev, h), nn.Tanh()]
                prev = h
            layers.append(nn.Linear(prev, out_dim))
            self.net = nn.Sequential(*layers)

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            return self.net(x)

    class ActorCritic(nn.Module):
        def __init__(
            self,
            state_dim: int,
            action_dim: int,
            hidden: tuple[int, ...] = (256, 256),
        ) -> None:
            super().__init__()
            self.actor_mean    = _MLP(state_dim, action_dim, hidden)
            self.actor_log_std = nn.Parameter(torch.zeros(action_dim))
            self.critic        = _MLP(state_dim, 1, hidden)

        def forward(
            self, state: torch.Tensor
        ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
            mean  = torch.tanh(self.actor_mean(state))
            std   = self.actor_log_std.exp().expand_as(mean)
            value = self.critic(state).squeeze(-1)
            return mean, std, value

        def act(
            self,
            state: torch.Tensor,
            deterministic: bool = False,
        ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
            mean, std, value = self(state)
            dist   = torch.distributions.Normal(mean, std)
            action = mean if deterministic else dist.sample()
            action = torch.clamp(action, -1.0, 1.0)
            log_prob = dist.log_prob(action).sum(-1)
            return action, log_prob, value


# ── Rollout buffer ─────────────────────────────────────────────────────────────

class RolloutBuffer:
    def __init__(self, size: int, state_dim: int, action_dim: int) -> None:
        self.size      = size
        self.states    = np.zeros((size, state_dim),  dtype=np.float32)
        self.actions   = np.zeros((size, action_dim), dtype=np.float32)
        self.log_probs = np.zeros(size,               dtype=np.float32)
        self.rewards   = np.zeros(size,               dtype=np.float32)
        self.values    = np.zeros(size,               dtype=np.float32)
        self.dones     = np.zeros(size,               dtype=np.float32)
        self.ptr       = 0

    def add(
        self,
        state: np.ndarray,
        action: np.ndarray,
        log_prob: float,
        reward: float,
        value: float,
        done: bool,
    ) -> None:
        i = self.ptr % self.size
        self.states[i]    = state
        self.actions[i]   = action
        self.log_probs[i] = log_prob
        self.rewards[i]   = reward
        self.values[i]    = value
        self.dones[i]     = float(done)
        self.ptr += 1

    def is_full(self) -> bool:
        return self.ptr >= self.size

    def reset(self) -> None:
        self.ptr = 0


# ── Agent ─────────────────────────────────────────────────────────────────────

class PPOAgent:
    """
    Proximal Policy Optimisation agent for AUVEnvironment.

    Continuous action space in [-1, 1] per dimension.
    """

    def __init__(
        self,
        state_dim: int,
        action_dim: int,
        lr: float = 3e-4,
        gamma: float = 0.99,
        gae_lambda: float = 0.95,
        clip_eps: float = 0.2,
        entropy_coef: float = 0.01,
        value_coef: float = 0.5,
        n_steps: int = 2048,
        batch_size: int = 64,
        n_epochs: int = 10,
        hidden: tuple[int, ...] = (256, 256),
        device: str = "auto",
    ) -> None:
        if not _TORCH:
            raise RuntimeError("torch is required for PPOAgent")

        self.gamma        = gamma
        self.gae_lambda   = gae_lambda
        self.clip_eps     = clip_eps
        self.entropy_coef = entropy_coef
        self.value_coef   = value_coef
        self.n_steps      = n_steps
        self.batch_size   = batch_size
        self.n_epochs     = n_epochs

        self.device = (
            torch.device("cuda" if torch.cuda.is_available() else "cpu")
            if device == "auto"
            else torch.device(device)
        )
        log.info("PPOAgent using device: %s", self.device)

        self.policy    = ActorCritic(state_dim, action_dim, hidden).to(self.device)
        self.optimizer = optim.Adam(self.policy.parameters(), lr=lr)
        self.buffer    = RolloutBuffer(n_steps, state_dim, action_dim)

        self._last_log_prob = 0.0
        self._last_value    = 0.0

    # ── inference ─────────────────────────────────────────────────────────────

    def select_action(
        self, state: np.ndarray, deterministic: bool = False
    ) -> np.ndarray:
        with torch.no_grad():
            t = torch.FloatTensor(state).unsqueeze(0).to(self.device)
            action, log_prob, value = self.policy.act(t, deterministic=deterministic)
        self._last_log_prob = float(log_prob.item())
        self._last_value    = float(value.item())
        return action.squeeze(0).cpu().numpy()

    def store_transition(
        self,
        state: np.ndarray,
        action: np.ndarray,
        reward: float,
        done: bool,
    ) -> None:
        self.buffer.add(
            state, action, self._last_log_prob, reward, self._last_value, done
        )

    # ── learning ──────────────────────────────────────────────────────────────

    def update(self) -> dict:
        """Run PPO update over the filled rollout buffer. Returns loss info."""
        if not self.buffer.is_full():
            return {}

        advantages, returns = self._compute_gae()

        states   = torch.FloatTensor(self.buffer.states).to(self.device)
        actions  = torch.FloatTensor(self.buffer.actions).to(self.device)
        old_lps  = torch.FloatTensor(self.buffer.log_probs).to(self.device)
        adv_t    = torch.FloatTensor(advantages).to(self.device)
        ret_t    = torch.FloatTensor(returns).to(self.device)
        adv_t    = (adv_t - adv_t.mean()) / (adv_t.std() + 1e-8)

        total_loss = 0.0
        n_batches  = 0

        for _ in range(self.n_epochs):
            idx = np.random.permutation(self.n_steps)
            for start in range(0, self.n_steps, self.batch_size):
                b = idx[start : start + self.batch_size]

                mean, std, values = self.policy(states[b])
                dist      = torch.distributions.Normal(mean, std)
                new_lps   = dist.log_prob(actions[b]).sum(-1)
                entropy   = dist.entropy().sum(-1).mean()

                ratio   = (new_lps - old_lps[b]).exp()
                clip_r  = torch.clamp(ratio, 1 - self.clip_eps, 1 + self.clip_eps)
                actor_loss  = -torch.min(ratio * adv_t[b], clip_r * adv_t[b]).mean()
                critic_loss = (ret_t[b] - values).pow(2).mean()
                loss = (
                    actor_loss
                    + self.value_coef  * critic_loss
                    - self.entropy_coef * entropy
                )

                self.optimizer.zero_grad()
                loss.backward()
                nn.utils.clip_grad_norm_(self.policy.parameters(), 0.5)
                self.optimizer.step()

                total_loss += loss.item()
                n_batches  += 1

        self.buffer.reset()
        return {"loss": total_loss / max(n_batches, 1)}

    def _compute_gae(self) -> tuple[np.ndarray, np.ndarray]:
        rewards = self.buffer.rewards
        values  = self.buffer.values
        dones   = self.buffer.dones
        adv     = np.zeros_like(rewards)
        last_adv = 0.0

        for t in reversed(range(self.n_steps)):
            if t + 1 < self.n_steps:
                next_val = values[t + 1] * (1 - dones[t])
            else:
                next_val = 0.0
            delta    = rewards[t] + self.gamma * next_val - values[t]
            adv[t]   = last_adv = delta + self.gamma * self.gae_lambda * (1 - dones[t]) * last_adv

        returns = adv + values
        return adv, returns

    # ── persistence ───────────────────────────────────────────────────────────

    def save(self, path: str | Path) -> None:
        torch.save(
            {
                "policy":    self.policy.state_dict(),
                "optimizer": self.optimizer.state_dict(),
            },
            path,
        )
        log.info("model saved → %s", path)

    def load(self, path: str | Path) -> None:
        ckpt = torch.load(path, map_location=self.device, weights_only=True)
        self.policy.load_state_dict(ckpt["policy"])
        self.optimizer.load_state_dict(ckpt["optimizer"])
        log.info("model loaded ← %s", path)
