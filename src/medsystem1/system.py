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

    def __init__(self, router: SafetyRouter | None = None, *, project_root=None, deployment_path=None):
        self.router = router or SafetyRouter()
        # These are administrator arguments, never fields accepted from DecideRequest.
        self._root = project_root if project_root is not None else _resource_root()
        self._bundle = load_bundle(self._root)
        from .core.orchestrator import build_local_runtime, LocalRuntime
        self._runtime = (build_local_runtime(self._root, deployment_path, bundle=self._bundle)
                         if deployment_path is not None else LocalRuntime())

    def route(self, request: RouteRequest) -> RouteDecision:
        return self.router.route(request)

    def decide(self, request: dict) -> dict:
        """Canonical request -> rules or explicitly administered review-only candidates.

        Default has zero provider calls. Configuration is frozen per instance;
        no cloud export or persistence. Invalid data raises a redacted fixed code.
        """
        try:
            snapshot = RequestModel.from_dict(request, self._bundle.schema_dir)
        except (ValidationError, ValueError, TypeError, KeyError, RecursionError):
            raise DecisionRequestError('invalid_request') from None
        # Import after package initialization: rules record the software version.
        from .core.orchestrator import evaluate
        return evaluate(snapshot.to_dict(), self._root, bundle=self._bundle, runtime=self._runtime)

