from __future__ import annotations

from .models import RouteDecision, RouteRequest
from .router import SafetyRouter


class MedSystem1:
    """Small facade around the safety router."""

    def __init__(self, router: SafetyRouter | None = None):
        self.router = router or SafetyRouter()

    def route(self, request: RouteRequest) -> RouteDecision:
        return self.router.route(request)
