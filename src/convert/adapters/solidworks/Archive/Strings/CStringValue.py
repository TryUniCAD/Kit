from dataclasses import dataclass as DataClass


# source text needs an explicit encoding before native lengths can be derived
@DataClass(frozen=True, slots=True)
class CStringValue:
    TextValue: str
    IsUnicode: bool

    # explicit types prevent silent coercion from changing the source string representation
    def __post_init__(self: "CStringValue") -> None:
        if type(self.TextValue) is not str or type(self.IsUnicode) is not bool:
            raise TypeError(
                "archive strings require text and an explicit encoding flag"
            )
