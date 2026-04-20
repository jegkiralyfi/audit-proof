class AuditProofError(Exception):
    """Base exception."""


class UnsupportedDomainError(AuditProofError):
    """Raised when a domain is not implemented in the PoC."""
