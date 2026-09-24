"""Public engine errors for invalid data, actions, and saved states."""


class CatalogError(ValueError):
    """Static game data is missing, conflicting, or invalid."""


class InvalidActionError(ValueError):
    """An action is not legal in the current state."""


class UnsupportedRuleError(ValueError):
    """The requested rule is outside the implemented engine subset."""


class StateFormatError(ValueError):
    """A serialized game state is invalid or incompatible."""
