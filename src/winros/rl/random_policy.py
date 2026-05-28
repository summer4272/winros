from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class RandomPolicy:
    action_dim: int
    low: float = -1.0
    high: float = 1.0
    seed: int | None = None

    def sample(self) -> np.ndarray:
        rng = np.random.default_rng(self.seed)
        return rng.uniform(self.low, self.high, size=self.action_dim)


class StatefulRandomPolicy:
    def __init__(
        self,
        action_dim: int,
        low: float = -1.0,
        high: float = 1.0,
        seed: int | None = None,
    ) -> None:
        self.action_dim = action_dim
        self.low = low
        self.high = high
        self._rng = np.random.default_rng(seed)

    def sample(self) -> np.ndarray:
        return self._rng.uniform(self.low, self.high, size=self.action_dim)
