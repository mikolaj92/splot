from __future__ import annotations


class SplotError(Exception):
    """Base class for Splot errors."""


class SplotProfileError(SplotError, ValueError):
    pass


class SplotValidationError(SplotError, ValueError):
    pass


class SplotRegistryError(SplotError, KeyError):
    pass


class SplotProviderError(SplotError, RuntimeError):
    pass


class SplotPolicyError(SplotError, RuntimeError):
    pass


class SplotStabilityError(SplotError, RuntimeError):
    pass


class SplotCompositionError(SplotError, RuntimeError):
    pass


class SplotReportError(SplotError, ValueError):
    pass
