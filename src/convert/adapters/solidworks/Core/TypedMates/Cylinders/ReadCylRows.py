from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadRows,
    ReadNodeName,
    RequireNode,
)
from convert.adapters.solidworks.Assembly.PlanarMates.PlanarContext import PlanarContext
from convert.adapters.solidworks.Core.TypedMates.Cylinders.CylChild import CylChild
from convert.adapters.solidworks.Core.TypedMates.Cylinders.ReadCylEnd import ReadCylEnd
from convert.adapters.solidworks.Core.TypedMates.Cylinders.CheckCylFacet import (
    CheckCylFacet,
)
from convert.adapters.solidworks.Core.TypedMates.Cylinders.CheckCylPair import (
    CheckCylPair,
)
from convert.adapters.solidworks.Core.TypedMates.Cylinders.MakeCylEntity import (
    MakeCylEntity,
)
from convert.adapters.solidworks.Core.TypedMates.Cylinders.MakeCylRule import (
    MakeCylRule,
)
from convert.adapters.solidworks.Core.TypedMates.MateProvenance import MateProvenance
from interchange import MateConstraint, MateEntity


# complete cylinder admission must preserve both actual serialized endpoint order and existing neutral rule identities
def ReadCylRows(
    NodeValue: ArchiveNode,
    Context: PlanarContext,
    ChildValue: CylChild,
    LegacyEntities: tuple[MateEntity, ...],
    LegacyRule: MateConstraint,
) -> tuple[tuple[MateEntity, ...], MateConstraint]:
    if str(LegacyRule.kind) != "concentric" or LegacyRule.name != ReadNodeName(
        NodeValue
    ):
        raise ValueError("concentric typed and legacy mate inventory differ")
    Endpoints = tuple(
        ReadCylEnd(
            Context,
            ChildValue,
            RequireNode(RowValue.get("o"), "moCylinderRef_w"),
            FieldInt(NodeValue.FieldsValue, "f08"),
            Index,
        )
        for Index, RowValue in enumerate(ReadRows(NodeValue.FieldsValue.get("f410")))
    )
    for RowValue in ReadRows(NodeValue.FieldsValue.get("f3c8")):
        CheckCylFacet(RequireNode(RowValue.get("o"), "moCylinderRef_w"), ChildValue)
    CheckCylPair(Endpoints, FieldInt(NodeValue.FieldsValue, "f3b4"))
    ProvenanceValue = MateProvenance(NodeValue)
    LegacyMap = {Value.id: Value for Value in LegacyEntities}
    Entities = tuple(
        MakeCylEntity(Value, ChildValue, LegacyRule, Index, ProvenanceValue, LegacyMap)
        for Index, Value in enumerate(Endpoints)
    )
    return Entities, MakeCylRule(NodeValue, LegacyRule, Entities, ProvenanceValue)
