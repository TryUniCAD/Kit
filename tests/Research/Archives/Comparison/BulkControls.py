from interchange.Enums.EnumValues import ValueKind
from interchange.Records.RecordParameter import Parameter, ParameterValue


# independently owned alternative controls make a changed dependency visible without changing scalar records
def MakeControls(Prefix: str) -> tuple[Parameter, ...]:
    return tuple(
        Parameter(
            Prefix + "distance" + str(Index),
            "authored distance",
            ParameterValue(Number, ValueKind.KLength, "mm"),
            owner_id=Prefix + "modifier",
        )
        for Index, Number in enumerate((0.5, 1.5))
    )
