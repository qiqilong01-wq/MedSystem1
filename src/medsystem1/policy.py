"""Immutable deployment catalog. Request data cannot redefine task risk/scope."""
from dataclasses import dataclass
import hashlib
from importlib.resources import files
import json
from pathlib import Path
from types import MappingProxyType


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate_policy_field')
        result[key] = value
    return result


def _resource_root():
    source = Path(__file__).resolve().parents[2]
    if (source / 'configs/v0.1/tasks.json').is_file():
        return source
    return files('medsystem1').joinpath('_data')


@dataclass(frozen=True)
class TaskDefinition:
    task_id: str
    risk: str
    capability: str
    labels: tuple[str, ...]


class TaskCatalog:
    def __init__(self):
        root = _resource_root()
        raw = root.joinpath('configs/v0.1/tasks.json').read_text(encoding='utf-8')
        catalog = json.loads(raw, object_pairs_hook=_unique_object)
        schema = json.loads(root.joinpath('schemas/v0.1/decision.schema.json').read_text(encoding='utf-8'))
        labels = {}
        for choice in schema['oneOf']:
            properties = choice['properties']
            value = properties['value']['anyOf'][0]
            labels[properties['task_id']['const']] = value.get('enum', value.get('items', {}).get('enum'))
        if set(catalog['tasks']) != set(labels):
            raise ValueError('catalog_schema_mismatch')
        tasks = {}
        for task_id, item in catalog['tasks'].items():
            risk = 'moderate' if task_id == 'urgency_to_review' else 'low'
            if item['base_risk'] != risk or item['labels'] != labels[task_id]:
                raise ValueError('catalog_schema_mismatch')
            capability = ('detect_missing_field' if task_id == 'missing_fields' else
                          'classify_intent' if task_id == 'urgency_to_review' else 'extract_structured_fact')
            tasks[task_id] = TaskDefinition(task_id, risk, capability, tuple(item['labels']))
        self.tasks = MappingProxyType(tasks)
        self.version = catalog['catalog_version']
        self.sha256 = hashlib.sha256(raw.encode()).hexdigest()

    def get(self, task_id):
        return self.tasks.get(task_id)
