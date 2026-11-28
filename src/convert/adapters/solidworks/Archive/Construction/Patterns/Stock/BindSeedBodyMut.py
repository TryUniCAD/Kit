from convert.adapters.solidworks.Archive.Construction.BodyScope.MakeBodyRef import (
    MakeBodyRef,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Stock.ReadSeedChain import (
    ReadSeedChain,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# selecting the immediate solid must retire it and retain the actual base lineage
def BindSeedBodyMut(
    RootValue: ArchiveNode,
    ProducerValue: ArchiveNode,
    SelectedValue: ArchiveNode,
    ConsumerValue: ArchiveNode,
    OutputValue: ArchiveNode,
    *,
    PriorValues: tuple[tuple[ArchiveNode, ArchiveNode], ...] = (),
) -> ArchiveNode:
    OwnersValue = (
        *reversed(PriorValues),
        (ProducerValue, SelectedValue),
        (ConsumerValue, OutputValue),
    )
    AtomIds = ReadSeedChain(RootValue, OwnersValue)
    Wrapper = MakeBodyRef(RootValue, OwnersValue[0][0], SelectedValue)
    Wrapper.FieldsValue.update(
        n110=len(AtomIds), f110=[{"v": AtomId} for AtomId in AtomIds]
    )
    ConsumerValue.FieldsValue.update(
        f544=1,
        has_f548=1,
        f548={"n": 1, "items": [{"o": Wrapper}]},
        has_f530=1,
        f530={"n": 1, "items": [{"o": SelectedValue}]},
    )
    SelectedValue.FieldsValue["f144"] = 1
    return Wrapper
