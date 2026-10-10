class ProviderContractError(ValueError):
    """Provider input/output violates the normalized data contract."""


class ProviderExecutionError(RuntimeError):
    """The upstream callable failed; no result authorizes further action."""


class DecisionRequestError(ValueError):
    """Fixed, redacted canonical-request error; contains no source or schema repr."""
    def __init__(self, code):
        self.code = code
        super().__init__(code)

