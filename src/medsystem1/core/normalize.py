"""Freeze validated inputs while preserving source text and code-point offsets."""
from dataclasses import dataclass, field

from ..wire_models import RequestModel


@dataclass(frozen=True)
class Evidence:
    source_id: str = field(repr=False)
    start: int
    end: int

    def to_dict(self) -> dict:
        return {'source_id': self.source_id, 'start': self.start, 'end': self.end}


@dataclass(frozen=True)
class Source:
    source_id: str = field(repr=False)
    kind: str
    text: str = field(repr=False)


@dataclass(frozen=True)
class Fact:
    field: str
    value: str = field(repr=False)
    assertion: str
    temporality: str
    subject: str
    evidence: tuple[Evidence, ...]


@dataclass(frozen=True)
class PatientState:
    state_id: str = field(repr=False)
    revision: int
    encounter_id: str = field(repr=False)
    language: str
    sources: tuple[Source, ...]
    facts: tuple[Fact, ...]


@dataclass(frozen=True)
class NormalizedRequest:
    state: PatientState
    tasks: tuple[str, ...]
    cloud_fallback_requested: bool


def normalize(request: RequestModel) -> NormalizedRequest:
    data = request.to_dict()
    state = data['patient_state']
    sources = tuple(Source(s['source_id'], s['kind'], s['text']) for s in state['sources'])
    facts = tuple(Fact(f['field'], f['value'], f['assertion'], f['temporality'], f['subject'],
                       tuple(Evidence(e['source_id'], int(e['start']), int(e['end']))
                             for e in f['evidence'])) for f in state['facts'])
    return NormalizedRequest(PatientState(state['state_id'], int(state['revision']),
                                         state['encounter_id'], state['language'], sources, facts),
                             tuple(data['tasks']), data['cloud_fallback_requested'])
