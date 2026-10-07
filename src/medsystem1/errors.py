class ProviderContractError(ValueError):
    """Provider input/output violates the normalized data contract."""


class ProviderExecutionError(RuntimeError):
    """The upstream callable failed; no result authorizes further action."""
