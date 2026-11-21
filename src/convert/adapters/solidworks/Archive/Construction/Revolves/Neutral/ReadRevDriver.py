from convert.adapters.solidworks.Archive.Construction.Styles.ReadStyleNum import (
    ReadStyleNum,
)
from interchange.Enums.EnumValues import ParameterRole, ValueKind
from interchange.Records.RecordParameter import Parameter


# each active native side needs its own authored radian parameter and actual feature owner
def ReadRevDriver(ParameterValue: Parameter, OwnerId: str, NameValue: str) -> float:
    if (
        ParameterValue.name != NameValue
        or ParameterValue.role != ParameterRole.KDriving
        or ParameterValue.owner_id != OwnerId
        or ParameterValue.expression is not None
        or ParameterValue.attributes
        or ParameterValue.value.kind != ValueKind.KAngle
        or ParameterValue.value.unit != "rad"
    ):
        raise ValueError(
            f"revolve construction requires its actual {NameValue} radian driver"
        )
    AngleValue = ReadStyleNum(ParameterValue.value.value, "revolve angle")
    if AngleValue <= 1e-8:
        raise ValueError("revolve angle must be positive through one full turn")
    return AngleValue
