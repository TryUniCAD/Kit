from dataclasses import dataclass as DataClass


# missing inherited objects need explicit references rather than fabricated graph nodes
@DataClass(frozen=True, slots=True)
class ExternalRef:
    IndexValue: int

    # reserved null and malformed indices cannot identify an external object
    def __post_init__(self) -> None:
        if type(self.IndexValue) is not int:
            raise TypeError("external archive object index must be an integer")
        if not 1 <= self.IndexValue <= 0x7FFFFFFF:
            raise ValueError("external archive object index exceeds the tag domain")
