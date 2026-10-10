from dataclasses import replace
from itertools import product
import math
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'src'))
from medsystem1.routing import Risk, Route, RouteContext, decide_route


class RoutingTests(unittest.TestCase):
    def auto_context(self):
        return RouteContext(risk=Risk.LOW, task_capability=True,
                            evidence_valid=True, auto_enabled=True,
                            calibration_valid=True, calibrated_probability=0.99)

    def cloud_context(self):
        return RouteContext(risk=Risk.LOW, any_result=False,
                            frontier_enabled=True, frontier_requested=True,
                            export_capability=True, privacy_cleared=True,
                            sanitized_payload_valid=True, frontier_healthy=True)

    def test_default_requires_review(self):
        self.assertEqual(decide_route(RouteContext()), Route.HUMAN_REVIEW)

    def test_risk_dominates_all_scores_rules_and_fallback(self):
        combinations = 0
        for risk, cap, rule, lock, cloud, p in product(
                Risk, (False, True), (False, True), (False, True),
                (False, True), (None, 0.2, 0.95, 1.0)):
            c = replace(self.auto_context(), risk=risk, task_capability=cap,
                        deterministic_result=rule, review_lock=lock,
                        calibrated_probability=p, frontier_enabled=cloud,
                        frontier_requested=cloud, export_capability=cloud,
                        privacy_cleared=cloud, sanitized_payload_valid=cloud,
                        frontier_healthy=cloud)
            if risk != Risk.LOW or lock:
                self.assertEqual(decide_route(c), Route.HUMAN_REVIEW)
            if not cap:
                self.assertNotIn(decide_route(c), (Route.LOCAL_AUTO, Route.RULES))
            combinations += 1
        self.assertEqual(combinations, 256)

    def test_threshold_boundary_and_missing_calibration(self):
        c = self.auto_context()
        self.assertEqual(decide_route(replace(c, calibrated_probability=0.9499)), Route.HUMAN_REVIEW)
        for p in (0.95, 0.9501):
            self.assertEqual(decide_route(replace(c, calibrated_probability=p)), Route.LOCAL_AUTO)
        for patch in ({'calibration_valid':False}, {'calibrated_probability':None},
                      {'auto_enabled':False}, {'task_capability':False}, {'evidence_valid':False}):
            self.assertEqual(decide_route(replace(c, **patch)), Route.HUMAN_REVIEW)

    def test_rules_still_require_capability_and_valid_evidence(self):
        c = RouteContext(risk=Risk.LOW, task_capability=True,
                         deterministic_result=True, evidence_valid=True)
        self.assertEqual(decide_route(c), Route.RULES)
        for patch in ({'output_valid':False}, {'review_lock':True}, {'out_of_domain':True},
                      {'task_capability':False}, {'evidence_valid':False}):
            self.assertEqual(decide_route(replace(c, **patch)), Route.HUMAN_REVIEW)

    def test_all_cloud_gates_required(self):
        c = self.cloud_context()
        self.assertEqual(decide_route(c), Route.FRONTIER_FALLBACK)
        for gate in ('frontier_enabled', 'frontier_requested', 'export_capability',
                     'privacy_cleared', 'sanitized_payload_valid', 'frontier_healthy'):
            self.assertEqual(decide_route(replace(c, **{gate:False})), Route.ABSTAIN)
        self.assertEqual(decide_route(replace(c, output_valid=False)), Route.HUMAN_REVIEW)
        self.assertEqual(decide_route(replace(c, scope_allowed=False)), Route.BLOCKED)

    def test_invalid_numbers_never_auto(self):
        for p in (math.nan, math.inf, -math.inf, -0.1, 1.1):
            self.assertEqual(decide_route(replace(self.auto_context(), calibrated_probability=p)), Route.HUMAN_REVIEW)
        self.assertEqual(decide_route(replace(self.auto_context(), threshold=math.nan)), Route.HUMAN_REVIEW)


if __name__ == '__main__':
    unittest.main()
