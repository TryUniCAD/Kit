from convert.adapters.solidworks.Archive.Construction.Styles.ReadStyleText import (
    ReadStyleText,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Model.AsmRootData import (
    AsmRootData,
)
from interchange.assembly.MateConstraint import MateConstraint
from interchange.assembly.MateEntity import MateEntity


# the dimensionless mate preserves explicit alignment lock and the original two endpoint identities
def ReadConcMate(
    Model: AsmRootData,
) -> tuple[MateConstraint, MateEntity, MateEntity, int, bool]:
    GraphValue = Model.GraphValue
    if len(GraphValue.mates) != 1 or len(GraphValue.mate_entities) != 2:
        raise ValueError("concentric preparation requires one mate and two endpoints")
    (MateValue,) = GraphValue.mates
    AlignValue = str(MateValue.alignment)
    if (
        str(MateValue.kind) != "concentric"
        or MateValue.owner_definition_id != Model.RootValue.id
        or AlignValue not in ("aligned", "anti_aligned")
        or type(MateValue.order) is not int
        or MateValue.order != 0
        or MateValue.suppressed is not False
        or MateValue.driving is not True
        or MateValue.value is not None
        or MateValue.parameter_ids
        or MateValue.provenance is not None
        or not ReadStyleText(MateValue.name, "concentric mate name")
    ):
        raise ValueError("concentric mate requires ordinary active driving intent")
    LockValue = MateValue.attributes.get("rotation_locked")
    if set(MateValue.attributes) != {"rotation_locked"} or type(LockValue) is not bool:
        raise ValueError("concentric rotation lock requires one explicit boolean")
    Entities = {Value.id: Value for Value in GraphValue.mate_entities}
    if (
        len(Entities) != 2
        or len(MateValue.entity_ids) != 2
        or set(MateValue.entity_ids) != set(Entities)
        or Model.GroupValue.mate_ids != (MateValue.id,)
    ):
        raise ValueError(
            "concentric endpoint or group membership differs from the mate"
        )
    First, Second = (Entities[KeyValue] for KeyValue in MateValue.entity_ids)
    return (
        MateValue,
        First,
        Second,
        1 if AlignValue == "aligned" else 2,
        LockValue,
    )
