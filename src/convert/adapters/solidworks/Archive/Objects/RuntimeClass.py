from dataclasses import dataclass as DataClass


# archive class identities need explicit schemas without feature construction defaults
@DataClass(frozen=True, slots=True)
class RuntimeClass:
    NameValue: str
    SchemaValue: int

    # malformed descriptors must fail before registry or map ownership is assigned
    def __post_init__(self) -> None:
        if type(self.NameValue) is not str or type(self.SchemaValue) is not int:
            raise TypeError("archive class name and schema have invalid types")
        if not 0 <= self.SchemaValue <= 0xFFFF:
            raise ValueError("archive class schema exceeds its unsigned short domain")
