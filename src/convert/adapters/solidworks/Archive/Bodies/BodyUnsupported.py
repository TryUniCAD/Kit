# compatibility callers must distinguish missing grammar from malformed admitted stream data
class BodyUnsupported(ValueError):
    __slots__ = ()
