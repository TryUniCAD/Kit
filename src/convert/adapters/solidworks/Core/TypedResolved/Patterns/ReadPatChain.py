from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.ReadStockAtom import (
    ReadStockAtom,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.ReadCutAtomId import (
    ReadCutAtomId,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.ReadManagedCutAtoms import (
    ReadCutAtoms,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.ReadSingleNode import (
    ReadSingleNode,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.Patterns.Cold.CheckColdPick import (
    CheckColdPick,
)
from convert.adapters.solidworks.Core.TypedResolved.ReadParents import ReadParents
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# the seed and pattern must successively consume the actual preceding managed atom
def ReadPatChain(
    LinkValue: NativeLink,
    Features: tuple[ArchiveNode, ...],
) -> tuple[tuple[int, ...], ArchiveNode]:
    PlateProfile, Plate, SeedProfile, SeedValue, Pattern = Features[-5:]
    PlateAtom = ReadStockAtom(Plate, False)
    SeedAtom = ReadStockAtom(SeedValue, True)
    Output = ReadStockAtom(Pattern, True)
    AtomsValue = (PlateAtom, SeedAtom, Output)
    AtomIds = tuple(
        ReadCutAtomId(AtomValue, Feature)
        for AtomValue, Feature in zip(
            AtomsValue, (Plate, SeedValue, Pattern), strict=True
        )
    )
    SeedList = RequireNative(Pattern.FieldsValue.get("f988"), "suObList")
    SelectedSeed = ReadSingleNode(SeedList.FieldsValue, "moICE_c")
    if (
        SelectedSeed is not SeedValue
        or ReadParents(Plate) != (PlateProfile,)
        or ReadParents(SeedValue) != (SeedProfile,)
        or Plate.FieldsValue.get("f810") != -1
        or Plate.FieldsValue.get("has_f548") != 0
        or SeedValue.FieldsValue.get("f810") != 0
        or len(set(AtomIds)) != 3
        or set(AtomsValue) != ReadCutAtoms(LinkValue)
        or tuple(AtomValue.FieldsValue.get("f144") for AtomValue in AtomsValue)
        != (1, 1, 0)
        or ReadSingleNode(SeedValue.FieldsValue.get("f530"), "moAtom_c")
        is not PlateAtom
        or ReadSingleNode(Pattern.FieldsValue.get("f530"), "moAtom_c") is not SeedAtom
    ):
        raise ValueError(
            "pattern history does not follow its actual joined seed and plate"
        )
    CheckColdPick(LinkValue, (Plate, SeedValue, Pattern), AtomIds, AtomsValue)
    return AtomIds, Output
