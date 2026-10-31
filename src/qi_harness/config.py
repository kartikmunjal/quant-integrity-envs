"""Prospective episode limits; no credentials or environment reads."""
from dataclasses import dataclass
import math


@dataclass(frozen=True)
class Limits:
    max_turns: int = 16
    max_completion_tokens: int = 2048
    max_total_tokens: int = 32768
    wall_seconds: float = 180
    tool_output_bytes: int = 16384
    transcript_bytes: int = 2097152

    def __post_init__(self):
        for name, value in vars(self).items():
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
                raise ValueError('limits must be positive finite numbers')
            if name != 'wall_seconds' and type(value) is not int:
                raise ValueError('count and byte limits must be integers')
