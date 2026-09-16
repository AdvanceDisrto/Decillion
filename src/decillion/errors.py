class DecillionError(Exception):
    """Base error for expected Decillion failures."""


class IntegrityError(DecillionError):
    """Ciphertext, metadata, or receipt verification failed."""


class AuthorizationError(DecillionError):
    """The caller is not authorized for the requested object."""


class AttestationError(AuthorizationError):
    """Trusted-execution attestation was absent or invalid."""


class LicensePolicyError(DecillionError):
    """A model license did not satisfy the configured policy."""
