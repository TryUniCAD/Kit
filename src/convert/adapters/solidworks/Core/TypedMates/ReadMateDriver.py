from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadNodeName,
    RequireNode,
)
from convert.adapters.solidworks.Core.TypedMates.ReadMateDim import ReadMateDim
from interchange import (
    MateConstraint,
    Parameter,
    ParameterRole,
    Provenance,
    ProvenanceSpan,
)


# the live length parameter belongs to the distance mate rather than its display cache
def ReadMateDriver(
    NodeValue: ArchiveNode, RuleValue: MateConstraint
) -> Parameter | None:
    if RuleValue.value is None:
        return None
    Dimension = ReadMateDim(NodeValue)
    LengthValue = RequireNode(Dimension.FieldsValue.get("f28"), "moLengthParameter_c")
    NativeId = FieldInt(Dimension.FieldsValue, "f50")
    StartValue, EndValue = LengthValue.StartOffset, LengthValue.EndOffset
    if StartValue is None or EndValue is None or EndValue <= StartValue:
        raise ValueError("typed mate driver lacks its native parameter span")
    return Parameter(
        id=f"{RuleValue.id}:parameter:{NativeId}",
        name=ReadNodeName(LengthValue),
        value=RuleValue.value,
        role=ParameterRole.DRIVING,
        owner_id=RuleValue.id,
        provenance=Provenance(
            adapter="sldasm",
            native_id=str(NativeId),
            spans=(
                ProvenanceSpan(
                    "Contents/Config-0-MatesList",
                    StartValue,
                    EndValue - StartValue,
                    "typed-length-parameter",
                ),
            ),
            confidence=1.0,
        ),
    )
