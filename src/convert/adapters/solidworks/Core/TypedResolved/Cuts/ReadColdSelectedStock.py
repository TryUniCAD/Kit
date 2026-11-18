from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Cuts.CheckCutWrapper import (
    CheckCutWrapper,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.ReadCutAtomId import (
    ReadCutAtomId,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ColdOutput.CheckColdAtom import (
    CheckColdAtom,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ColdOutput.FindColdAtom import (
    FindColdAtom,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ColdOutput.ReadColdBoss import (
    ReadColdBoss,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink


# a fresh through cut selects its sole managed stock without transmitting either an input mesh or a result atom
def ReadColdSelectedStock(
    LinkValue: NativeLink, BossValue: ArchiveNode, CutValue: ArchiveNode
) -> tuple[ArchiveNode, int]:
    Atom = FindColdAtom(LinkValue)
    if Atom is None or ReadColdBoss(LinkValue, Atom) is not BossValue:
        raise ValueError("cold selected cut lacks its actual sole stock producer")
    CheckColdAtom(Atom, ImplicitName=True)
    AtomId = ReadCutAtomId(Atom, BossValue)
    CheckCutWrapper(
        LinkValue.ConfigValue.RootValue, BossValue, CutValue, AtomId, Cold=True
    )
    return Atom, AtomId
