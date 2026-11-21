from convert.adapters.solidworks.Archive.Construction.BodyNames.CheckColdFresh import (
    CheckColdFresh,
)
from convert.adapters.solidworks.Archive.Construction.BodyNames.MakeColdAtom import (
    MakeColdAtom,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt


# one shared generated atom must own both the manager member and the producing feature output without copying a saved identity
def NameOutputMut(CandidateValue: PartCandidate, NameValue: str) -> ArchiveNode:
    ManagerValue = CheckColdFresh(CandidateValue)
    AtomId = FieldInt(ManagerValue, "f260") + 1
    FeatureValue = CandidateValue.BossValue.FeatureValue
    AtomValue = MakeColdAtom(NameValue, AtomId, FeatureValue)
    MembersValue = [{"o": AtomValue}]
    ManagerValue.update(f260=AtomId, n6c=len(MembersValue), atoms=MembersValue)
    FeatureValue.FieldsValue.update(
        has_f528=1,
        f528={"n": len(MembersValue), "items": [{"o": AtomValue}]},
        n494=len(MembersValue),
        f498=[{"v": AtomId}],
    )
    return AtomValue
