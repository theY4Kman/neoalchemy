class CypherAlchemyError(Exception):
    """Base CypherAlchemy error"""


class ArgumentError(CypherAlchemyError):
    """Raised when an invalid or conflicting function argument is supplied.

    This error generally corresponds to construction time state errors.

    """


class UnsupportedCompilationError(CypherAlchemyError):
    pass
