"""Immutable, Schema-backed wire models; no second handwritten field schema."""
from dataclasses import dataclass, field
import json
from pathlib import Path

from .contracts import validate_request, validate_response


@dataclass(frozen=True)
class RequestModel:
    _json: str = field(repr=False)

    @classmethod
    def from_dict(cls, data: dict, schema_dir: Path) -> 'RequestModel':
        encoded=json.dumps(data, ensure_ascii=False, allow_nan=False)
        validate_request(json.loads(encoded), schema_dir)
        return cls(encoded)

    def to_dict(self) -> dict:
        return json.loads(self._json)


@dataclass(frozen=True)
class ResponseModel:
    _json: str = field(repr=False)

    @classmethod
    def from_dict(cls, data: dict, request: RequestModel, schema_dir: Path) -> 'ResponseModel':
        encoded=json.dumps(data, ensure_ascii=False, allow_nan=False)
        validate_response(json.loads(encoded), request.to_dict(), schema_dir)
        return cls(encoded)

    def to_dict(self) -> dict:
        return json.loads(self._json)
