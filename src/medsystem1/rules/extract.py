"""Small fully-matched Chinese grammar. Unsupported text never proves low risk."""
from dataclasses import dataclass
from math import isfinite
import re

from ..core.normalize import Evidence, PatientState

SIDE = {'左眼': 'left', '右眼': 'right', '双眼': 'bilateral', '两眼': 'bilateral'}
SYMPTOMS = {'闪光': 'photopsia', '闪光感': 'photopsia', '飞蚊': 'floaters',
            '飞蚊症': 'floaters', '黑影飘动': 'floaters'}
NUM = r'(?:\d+(?:\.\d+)?|[一二三四五六七八九十两]+|半)'
DURATION = rf'{NUM}(?:小时|星期|个月|天|日|周|月|年)'
COMPLAINT = re.compile(rf'(左眼|右眼|双眼|两眼)(?:看东西)?(?:视物模糊|模糊)({DURATION})?')
SYMPTOM = re.compile(r'(左眼|右眼|双眼|两眼)?(现在否认|目前否认|否认|没有|无|不确定是否有|不确定有|可能有|还有|目前有|有)(.+)')
RECENT_CHANGE = re.compile(r'(昨天|今天|昨日)(?:开始)?(?:明显)?(?:加重|变化)')


@dataclass(frozen=True)
class Observation:
    field: str
    value: str
    subject: str
    temporality: str
    evidence: Evidence


@dataclass(frozen=True)
class Extraction:
    values: tuple[tuple[str, object], ...]
    observations: tuple[Observation, ...]
    unsupported: tuple[Evidence, ...]
    ambiguous: bool
    recent_change: bool
    severe_cue: bool
    fact_conflict: bool

    def value(self, task):
        value = dict(self.values)[task]
        return list(value) if isinstance(value, tuple) else value


def _number(raw):
    if raw == '半':
        return .5
    if re.fullmatch(r'\d+(?:\.\d+)?', raw):
        return float(raw)
    digits = dict(zip('一二三四五六七八九两', (1,2,3,4,5,6,7,8,9,2)))
    if raw in digits:
        return digits[raw]
    if raw == '十':
        return 10
    if re.fullmatch(r'[一二三四五六七八九]?十[一二三四五六七八九]?',raw):
        a,b=raw.split('十')
        return digits.get(a,1)*10+digits.get(b,0)
    return None


def _days(raw):
    m = re.fullmatch(rf'({NUM})(小时|星期|个月|天|日|周|月|年)', raw)
    number = _number(m[1]) if m else None
    if number is None or not isfinite(number) or number <= 0:
        return None
    result=number * {'小时':1/24,'星期':7,'周':7,'天':1,'日':1,'个月':30,'月':30,'年':365}[m[2]]
    return result if isfinite(result) else None


def _clauses(source):
    # Each source has its own subject context. Original source is never rewritten.
    start = 0
    separators = list(re.finditer(r'[，,；;。!！?？\n\r]|(?<!\d)\.|\.(?!\d)', source.text))
    for end in [m.start() for m in separators] + [len(source.text)]:
        raw = source.text[start:end]
        trimmed = raw.strip()
        if trimmed:
            offset = start+len(raw)-len(raw.lstrip())
            yield trimmed, Evidence(source.source_id,offset,offset+len(trimmed))
        start = end+1


def extract(state: PatientState, required_fields: tuple[str, ...]) -> Extraction:
    observations, unsupported = [], []
    ambiguous = state.language != 'zh-CN'
    recent_change = False
    severe_cue = False
    for source in state.sources:
        subject = 'unknown'
        clauses=list(_clauses(source))
        if not clauses:
            unsupported.append(Evidence(source.source_id,0,len(source.text)))
        for clause, evidence in clauses:
            content = clause
            for prefix, role in (('患者','patient'),('家属','other'),('母亲','other'),('父亲','other')):
                if content.startswith(prefix):
                    subject,content=role,content[len(prefix):]
                    break
            if content.startswith(('但','但是')):
                content=re.sub(r'^但是|^但','',content)
            temporality = 'current'
            for prefix in ('过去','曾经','既往','曾'):
                if content.startswith(prefix):
                    temporality,content='historical',content[len(prefix):]
                    break
            if content.startswith(('现在','目前')) and not content.startswith(('现在否认','目前否认','目前有')):
                content=content[2:]
            matched = False
            candidate = []
            if m := COMPLAINT.fullmatch(content):
                candidate.append(('laterality',SIDE[m[1]]))
                if m[2]:
                    if _days(m[2]) is None:
                        ambiguous=True
                    else:
                        candidate.append(('symptom_duration',m[2]))
                matched=True
            elif m := SYMPTOM.fullmatch(content):
                words=re.split(r'和|及|、',m[3])
                if words and all(w in SYMPTOMS for w in words):
                    value='absent' if m[2] in ('现在否认','目前否认','否认','没有','无') else (
                        'unknown' if m[2] in ('不确定是否有','不确定有','可能有') else 'present')
                    candidate.extend((SYMPTOMS[w],value) for w in words)
                    if m[1]:
                        candidate.append(('laterality',SIDE[m[1]]))
                    ambiguous |= value == 'unknown'
                    matched=True
            elif RECENT_CHANGE.fullmatch(content):
                if subject == 'patient' and temporality=='current':
                    recent_change=True
                    severe_cue=True
                matched=True
            elif re.fullmatch(r'(?:左眼或右眼记不清|眼别和持续时间不详|眼别不详|持续时间不详)',content):
                ambiguous=True
                matched=True
            elif m := re.fullmatch(r'(?:先说|又说)(左眼|右眼)',content):
                candidate.append(('laterality',SIDE[m[1]]))
                ambiguous=True
                matched=True
            elif content=='同一主诉无法确认':
                ambiguous=True
                matched=True
            elif m := re.fullmatch(r'视力([01](?:\.\d+)?)',content):
                candidate.append(('visual_acuity',m[1]))
                matched=True
            elif content in ('检查已记录','眼底检查已记录'):
                candidate.append(('examination','recorded'))
                matched=True
            elif content in ('视力未记录','检查未记录','眼底检查未记录'):
                matched=True
            if not matched or state.language != 'zh-CN':
                unsupported.append(evidence)
            if subject=='unknown':
                ambiguous=True
            # Review cues in unsupported text cannot be masked by requesting fewer tasks.
            if subject != 'other' and temporality=='current' and re.search(r'看不见|幕帘|遮挡|突然下降|突然失明',content):
                severe_cue=True
            for f,v in candidate:
                observations.append(Observation(f,v,subject,temporality,evidence))

    current=[o for o in observations if o.subject=='patient' and o.temporality=='current']
    if not any(o.subject=='patient' for o in observations):
        ambiguous=True
    def labels(field):
        return {o.value for o in current if o.field==field}
    if len(labels('visual_acuity'))>1:
        ambiguous=True
    def combine(field):
        v=labels(field)
        return next(iter(v)) if len(v)==1 else ('conflicting' if len(v)>1 else 'unknown')
    values={k:combine(k) for k in ('laterality','photopsia','floaters')}
    durations=labels('symptom_duration')
    ds={_days(d) for d in durations}
    if len(ds)>1:
        temporal='conflicting'
    elif ds:
        day=next(iter(ds))
        temporal=('longstanding_with_recent_change' if day>7 and recent_change else
                  'longstanding' if day>7 else 'recent')
    else:
        # A change cue alone does not establish the underlying complaint duration.
        temporal='unknown'
    values['temporal_classification']=temporal

    fact_conflict=False
    for fact in state.facts:
        compatible=[o for o in observations if o.field==fact.field and o.value==fact.value
                    and o.subject==fact.subject and o.temporality==fact.temporality
                    and (('negated' if o.value=='absent' else 'uncertain' if o.value=='unknown' else 'affirmed')==fact.assertion)
                    and any(e.source_id==o.evidence.source_id and e.start<=o.evidence.start
                            and e.end>=o.evidence.end for e in fact.evidence)]
        if not compatible:
            fact_conflict=True
            ambiguous=True
            task='temporal_classification' if fact.field=='symptom_duration' else fact.field
            if fact.subject=='patient' and fact.temporality=='current' and task in values:
                values[task]='conflicting'

    known={'laterality':values['laterality'] not in ('unknown','conflicting'),
           'symptom_duration':values['temporal_classification'] not in ('unknown','conflicting'),
           'visual_acuity':len(labels('visual_acuity'))==1,
           'examination':bool(labels('examination'))}
    values['missing_fields']=tuple(f for f in required_fields if not known[f])
    return Extraction(tuple(values.items()),tuple(observations),tuple(unsupported),ambiguous,
                      recent_change,severe_cue,fact_conflict)
