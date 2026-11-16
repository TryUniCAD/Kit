from dataclasses import dataclass as DataClass


# unresolved prefix classes need identities without fabricated wire schemas
@DataClass(frozen=True, slots=True)
class ExternalClass:
    NameValue: str
    IndexValue: int

    # external binding errors must surface before any reference bytes are emitted
    def __post_init__(self) -> None:
        if type(self.NameValue) is not str or type(self.IndexValue) is not int:
            raise TypeError("external archive class has invalid name or index types")
        if not 1 <= self.IndexValue <= 0x7FFFFFFF:
            raise ValueError("external archive class index exceeds the tag domain")
