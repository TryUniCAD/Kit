from convert.adapters.solidworks.Archive.Construction.Assembly.Headers.AsmTargetStamps import (
    AsmTargetStamps,
)
from convert.adapters.solidworks.Archive.Construction.AssemblyTargets.TargetDocument import (
    TargetDocument,
)
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt


# resolved part and assembly references share update ownership while assembly geometry and transform stamps depend on the actual child graph
def TargetStamps(TargetValue: TargetDocument) -> dict[str, int]:
    RootValue = TargetValue.RootValue
    if RootValue.ClassValue.NameValue == "moPart_c":
        GeometryValue, TransformValue = FieldInt(RootValue.FieldsValue, "f1300"), 101
    elif RootValue.ClassValue.NameValue == "moAssembly_c":
        GeometryValue, TransformValue = AsmTargetStamps(RootValue)
    else:
        raise ValueError("ordinary placement requires an actual part or assembly model")
    return {
        "f3e0": FieldInt(TargetValue.HeaderValue.FieldsValue, "f40"),
        "f3e8": FieldInt(TargetValue.HeaderValue.FieldsValue, "f48"),
        "f3f0": 102,
        "f3f4": GeometryValue,
        "f3f8": TransformValue,
    }
