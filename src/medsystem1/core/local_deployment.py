"""Trusted administrator configuration; loading never contacts a provider."""
from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path
from urllib.parse import urlsplit

from jsonschema.exceptions import ValidationError

from ..bounded import BoundedProviderError
from ..contracts import parse_request_json, validate_schema
from .config import load_bundle


@dataclass(frozen=True)
class LocalDeployment:
    _json: str = field(repr=False)
    _catalog_json: str = field(repr=False)
    config_sha256: str

    @property
    def settings(self):
        return json.loads(self._json)

    @property
    def catalog(self):
        return json.loads(self._catalog_json)


def load_local_deployment(root: Path, path: Path | None = None) -> LocalDeployment:
    """root/path are deployment-owned, never fields of a clinical request.

    Attestations are administrator assertions about independently checked local
    artifacts/launch settings, not remote cryptographic attestation. /health does
    not expose revisions or strict-window at the pinned upstream revision.
    """
    try:
        raw = (path or root/'configs/v0.1/local-deployment.disabled.json').read_bytes()
        if len(raw) > 64*1024:
            raise ValueError('deployment_limit')
        config = parse_request_json(raw)
        validate_schema(config, 'local.schema.json', root/'schemas/deployment/v0.1')
        if not 1 <= urlsplit(config['endpoint']).port <= 65535:
            raise ValueError('deployment_endpoint')
        bundle = load_bundle(root)
        registry = parse_request_json((root/'configs/v0.1/providers.json').read_bytes())['strands']
        if config['enabled']:
            if (config['code_revision'] != registry['code_revision']
                    or config['model_revision'] != registry['verified_model_release_revision']
                    or registry['base_revision'] is None
                    or config['base_revision'] != registry['base_revision']
                    or config['model_id'] != registry['model_id']
                    or config['base_id'] != registry['base_id']):
                raise ValueError('deployment_revision_mismatch')
        return LocalDeployment(json.dumps(config, allow_nan=False),
                               json.dumps(bundle.catalog, allow_nan=False),
                               hashlib.sha256(raw).hexdigest())
    except (OSError, ValueError, TypeError, KeyError, RecursionError, ValidationError):
        raise BoundedProviderError('capability_missing') from None
