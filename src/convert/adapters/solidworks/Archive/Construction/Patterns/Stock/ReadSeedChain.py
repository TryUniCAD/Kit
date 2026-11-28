from convert.adapters.solidworks.Archive.Construction.Model.RequireRootNode import (
    RequireRootNode,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadRows,
    RequireNode,
    RequireRecord,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.CheckCutWrapper import (
    CheckCutWrapper,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.ReadStockAtom import (
    ReadStockAtom,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.ReadCutAtomId import (
    ReadCutAtomId,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.ReadSingleNode import (
    ReadSingleNode,
)


# merge selection must reference only the latest live solid and its real base producer
def ReadSeedChain(
    RootValue: ArchiveNode, OwnersValue: tuple[tuple[ArchiveNode, ArchiveNode], ...]
) -> tuple[int, ...]:
    RequireRootNode(RootValue, "moPart_c")
    if len(OwnersValue) not in (2, 3):
        raise ValueError("raised seed requires its plate and at most one later pattern")
    TypesValue = ("moExtrusion_c", "moICE_c", "moLPattern_c")[: len(OwnersValue)]
    for Index, ((FeatureValue, AtomValue), ClassName) in enumerate(
        zip(OwnersValue, TypesValue, strict=True)
    ):
        OwnedFeature = RequireNode(FeatureValue, ClassName)
        if (
            OwnedFeature.FieldsValue.get("owner") is not RootValue
            or ReadStockAtom(OwnedFeature, Index == 1 and len(OwnersValue) == 3)
            is not AtomValue
        ):
            raise ValueError(
                "cannot consume a crossed, reused or non-current raised-seed atom"
            )
    AtomsValue = tuple(AtomValue for _, AtomValue in OwnersValue)
    AtomIds = tuple(
        ReadCutAtomId(AtomValue, FeatureValue)
        for FeatureValue, AtomValue in OwnersValue
    )
    Manager = RequireRecord(RootValue.FieldsValue.get("fd88"))
    Current = tuple(ItemValue.get("o") for ItemValue in ReadRows(Manager.get("atoms")))
    Consumer = OwnersValue[-1][0]
    if (
        any(
            AfterId != BeforeId + 1
            for BeforeId, AfterId in zip(AtomIds[:-1], AtomIds[1:], strict=True)
        )
        or Current != AtomsValue
        or FieldInt(Manager, "n6c") != len(AtomsValue)
        or FieldInt(Manager, "f260") != AtomIds[-1]
        or any(
            FieldInt(AtomValue.FieldsValue, SlotName) != 0
            for AtomValue in AtomsValue
            for SlotName in ("f180", "f188", "f1b0")
        )
        or tuple(FieldInt(AtomValue.FieldsValue, "f144") for AtomValue in AtomsValue)
        != (1,) * (len(OwnersValue) - 2) + (0, 0)
        or FieldInt(Consumer.FieldsValue, "has_f548") != 0
    ):
        raise ValueError(
            "cannot consume a crossed, reused or non-current raised-seed atom"
        )
    if len(OwnersValue) == 3:
        SeedValue = OwnersValue[1][0]
        if (
            ReadSingleNode(SeedValue.FieldsValue.get("f530"), "moAtom_c")
            is not AtomsValue[0]
        ):
            raise ValueError("raised seed must have consumed its actual base atom")
        CheckCutWrapper(
            RootValue, OwnersValue[0][0], SeedValue, AtomIds[0], IsCold=True
        )
    return tuple(reversed(AtomIds[:-1]))
