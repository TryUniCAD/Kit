# a distinct error type lets callers separate creo problems from ours
class CreoFormat(ValueError):
    __slots__ = ()
