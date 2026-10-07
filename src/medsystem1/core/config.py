"""Load a trusted repository bundle, and check catalog against canonical Schema."""
from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path

from ..contracts import schema_registry, validate_schema


@dataclass(frozen=True)
class Bundle:
    schema_dir: Path
    _policy_json: str = field(repr=False)
    _catalog_json: str = field(repr=False)
    config_sha256: str

    @property
    def policy(self):
        return json.loads(self._policy_json)

    @property
    def catalog(self):
        return json.loads(self._catalog_json)


def load_bundle(project_root: Path) -> Bundle:
    """Root is deployment-owned, never taken from a DecideRequest."""
    schema_dir = project_root / 'schemas/v0.1'
    policy_bytes = (project_root / 'configs/v0.1/policy.json').read_bytes()
    catalog_bytes = (project_root / 'configs/v0.1/tasks.json').read_bytes()
    policy, catalog = json.loads(policy_bytes), json.loads(catalog_bytes)
    validate_schema(policy, 'policy.schema.json', schema_dir)
    schemas, _ = schema_registry(schema_dir)
    choices = schemas['decision.schema.json']['oneOf']
    schema_labels = {}
    for choice in choices:
        p = choice['properties']
        value = p['value']['anyOf'][0]
        schema_labels[p['task_id']['const']] = value.get('enum', value.get('items', {}).get('enum'))
    if set(catalog['tasks']) != set(schema_labels) or set(policy['tasks']) != set(schema_labels):
        raise ValueError('catalog_task_mismatch')
    for task, labels in schema_labels.items():
        if catalog['tasks'][task]['labels'] != labels:
            raise ValueError('catalog_labels_mismatch')
        expected_risk = 'moderate' if task == 'urgency_to_review' else 'low'
        if catalog['tasks'][task]['base_risk'] != expected_risk:
            raise ValueError('catalog_risk_mismatch')
    required_fields = catalog['documentation_profile']['required_fields']
    if required_fields != schema_labels['missing_fields']:
        raise ValueError('documentation_profile_mismatch')
    if catalog['schema_version'] != policy['schema_version']:
        raise ValueError('catalog_schema_mismatch')
    if policy['total_timeout_ms'] < policy['local']['timeout_ms']:
        raise ValueError('invalid_deadline_budget')
    return Bundle(schema_dir, policy_bytes.decode('utf-8'), catalog_bytes.decode('utf-8'),
                  hashlib.sha256(policy_bytes + b'\x00' + catalog_bytes).hexdigest())
