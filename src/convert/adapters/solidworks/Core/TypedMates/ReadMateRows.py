from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.PlanarContext import PlanarContext
from convert.adapters.solidworks.Core.TypedMates.PublicMateEnv import PublicMateEnv
from convert.adapters.solidworks.Core.TypedMates.ReadPublicMate import ReadPublicMate
from interchange import MateConstraint, MateEntity


# ordered typed roots must keep each existing neutral mate identity and its complete selections
def ReadMateRows(
    NodesValue: tuple[ArchiveNode, ...],
    Context: PlanarContext,
    EnvValue: PublicMateEnv,
    LegacyRules: tuple[MateConstraint, ...],
    LegacyEntities: tuple[MateEntity, ...],
) -> tuple[tuple[MateEntity, ...], tuple[MateConstraint, ...]]:
    Existing = {Value.id: Value for Value in LegacyEntities}
    MateRows = tuple(
        ReadPublicMate(NodeValue, Context, EnvValue, LegacyValue, Existing)
        for NodeValue, LegacyValue in zip(NodesValue, LegacyRules, strict=True)
    )
    return (
        tuple(Value for Entities, _ in MateRows for Value in Entities),
        tuple(RuleValue for _, RuleValue in MateRows),
    )
