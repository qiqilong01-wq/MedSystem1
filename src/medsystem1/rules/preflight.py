"""Whole-input engineering review gates, independent of requested task IDs."""
from dataclasses import dataclass

from ..routing import Risk
from .extract import Extraction


@dataclass(frozen=True)
class ReviewGuard:
    risk: Risk
    review_lock: bool
    reasons: tuple[str,...]


def preflight(extracted: Extraction) -> ReviewGuard:
    conflict=extracted.fact_conflict or any(v=='conflicting' for _,v in extracted.values)
    positive=any(o.field in ('photopsia','floaters') and o.value=='present'
                 and o.subject=='patient' and o.temporality=='current' for o in extracted.observations)
    reasons=[]
    if conflict:
        reasons.append('input_conflict')
    if extracted.unsupported or extracted.ambiguous:
        reasons.append('out_of_domain')
    if positive or extracted.severe_cue or extracted.recent_change:
        reasons.append('risk_requires_review')
        return ReviewGuard(Risk.HIGH,True,tuple(reasons))
    if conflict or extracted.unsupported or extracted.ambiguous:
        return ReviewGuard(Risk.UNKNOWN,True,tuple(reasons))
    return ReviewGuard(Risk.LOW,False,())
