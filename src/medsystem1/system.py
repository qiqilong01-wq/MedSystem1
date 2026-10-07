from __future__ import annotations

from .models import RouteDecision, RouteRequest
from .router import SafetyRouter
from .core.config import load_bundle
from .errors import DecisionRequestError
from .policy import _resource_root
from .wire_models import RequestModel
from jsonschema.exceptions import ValidationError


class MedSystem1:
    """Separate legacy advisory routing and canonical, request-scoped local rules."""

    def __init__(self, router: SafetyRouter | None = None):
        self.router = router or SafetyRouter()
        self._root = _resource_root()
        self._bundle = load_bundle(self._root)

    def route(self, request: RouteRequest) -> RouteDecision:
        return self.router.route(request)

    def decide(self, request: dict) -> dict:
        """Canonical JSON Schema request -> evidence-backed rules/review envelope.

        Never calls a model, exports data or persists Patient State. Configuration
        is frozen per instance. Invalid caller data raises a redacted fixed code.
        """
        try:
            snapshot = RequestModel.from_dict(request, self._bundle.schema_dir)
        except (ValidationError, ValueError, TypeError, KeyError):
            raise DecisionRequestError('invalid_request') from None
        # Import after package initialization: rules record the software version.
        from .core.rules_engine import evaluate_rules
        return evaluate_rules(snapshot.to_dict(), self._root, bundle=self._bundle)

