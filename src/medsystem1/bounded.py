"""Canonical provider candidates; never a routing decision or execution grant."""
from dataclasses import dataclass, field
import json
from typing import Protocol


class BoundedProviderError(RuntimeError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class BoundedDescriptor:
    provider_id: str
    model_id: str
    code_revision: str
    model_revision: str
    base_revision: str
    supported_tasks: tuple[str, ...]
    locality: str = 'local'


@dataclass(frozen=True)
class BoundedAnswer:
    task_id: str
    label: str
    native_score: float
    _probabilities_json: str = field(repr=False)

    @property
    def probabilities(self):
        return json.loads(self._probabilities_json)

    @property
    def selected_probability(self):
        return self.probabilities[self.label]


@dataclass(frozen=True)
class BoundedResult:
    answers: tuple[BoundedAnswer, ...]
    descriptor: BoundedDescriptor
    latency_ms: float
    # This adapter only accepts an administrator-attested strict-window server.
    # Upstream cannot report evidence, calibration eligibility or routing authority.


class LocalDecisionProvider(Protocol):
    descriptor: BoundedDescriptor

    def health(self, *, timeout_ms: int = 2000) -> bool: ...

    def decide(self, state: str, task_ids: tuple[str, ...], *, timeout_ms: int) -> BoundedResult: ...
