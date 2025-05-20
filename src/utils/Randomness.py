# -*- coding: utf-8 -*-
# Copyright (c) 2024, Harry Huang
# @ MIT License
import random
from typing import Optional, Sequence, TypeVar

_T = TypeVar("_T")


class Randomness:
    @staticmethod
    def about(
        base: float, max_noise: float = 1.0, min_value: Optional[float] = 0.0, max_value: Optional[float] = None
    ):
        if min_value is not None and max_value is not None and min_value > max_value:
            raise ValueError("min_value cannot be larger than max_value")
        value = base + (random.random() - 0.5) * 2.0 * max_noise
        if min_value is not None:
            value = max(value, min_value)
        if max_value is not None:
            value = min(value, max_value)
        return value

    @staticmethod
    def choose(options: Sequence[_T], k: int = 1):
        return random.choices(options, k=k)
