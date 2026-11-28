from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadPrincAxis import (
    ReadPrincAxis,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.RequireAsm import RequireAsm
from interchange.document.Models.DocumentModel import CadDocument
from interchange.geometry.Models.SupportPlane import SupportPlane


# mate endpoints need actual independently named principal datums instead of invented identifiers derived from captions
def ReadAsmPlanes(Document: CadDocument) -> dict[str, SupportPlane]:
    RequireAsm(
        len(Document.support_planes) == 3,
        "all three actual principal plane ids are required",
    )
    ResultValue: dict[str, SupportPlane] = {}
    for Value in Document.support_planes:
        RequireAsm(
            Value.support_selection_id is None
            and Value.offset_parameter_id is None
            and Value.provenance is None
            and not Value.attributes,
            "principal plane has unsupported support or extensions",
        )
        AxisValue = ReadPrincAxis(Value.transform)
        RequireAsm(
            AxisValue not in ResultValue and bool(Value.id) and bool(Value.name),
            "principal plane roles are ambiguous or empty",
        )
        ResultValue[AxisValue] = Value
    RequireAsm(set(ResultValue) == set("xyz"), "principal plane roles are incomplete")
    return ResultValue
