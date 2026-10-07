from __future__ import annotations

from math import isfinite
from numbers import Real


def unit_interval(value: object, *, name: str) -> float:
    """Validate an actual finite number; bool is not a confidence signal."""
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{name} must be a finite number between 0 and 1")
    if not 0 <= value <= 1 or not isfinite(value):
        raise ValueError(f"{name} must be a finite number between 0 and 1")
    return float(value)


def provider_confidence(value: object) -> float:
    """Allow numeric strings from upstream payloads, then validate the range."""
    if isinstance(value, str):
        try:
            value = float(value)
        except ValueError as exc:
            raise ValueError("provider confidence must be a finite number between 0 and 1") from exc
    return unit_interval(value, name="provider confidence")
