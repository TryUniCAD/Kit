from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.PlanarContext import PlanarContext
from convert.adapters.solidworks.Core.TypedMates.PublicMateEnv import PublicMateEnv
from convert.adapters.solidworks.Core.TypedMates.ReadMateDriver import ReadMateDriver
from convert.adapters.solidworks.Core.TypedMates.ReadPublicMate import ReadPublicMate
from interchange import MateConstraint, MateEntity, Parameter


# ordered typed roots must keep each existing neutral mate identity and its complete selections
def ReadMateRows(
    NodesValue: tuple[ArchiveNode, ...],
    Context: PlanarContext,
    EnvValue: PublicMateEnv,
    LegacyRules: tuple[MateConstraint, ...],
    LegacyEntities: tuple[MateEntity, ...],
) -> tuple[tuple[MateEntity, ...], tuple[MateConstraint, ...], tuple[Parameter, ...]]:
    Existing = {Value.id: Value for Value in LegacyEntities}
    Entities: list[MateEntity] = []
    Rules: list[MateConstraint] = []
    Parameters: list[Parameter] = []
    for NodeValue, LegacyValue in zip(NodesValue, LegacyRules, strict=True):
        Picks, RuleValue = ReadPublicMate(NodeValue, Context, EnvValue, LegacyValue, Existing)
        ParameterValue = ReadMateDriver(NodeValue, RuleValue)
        if ParameterValue is not None:
            RuleValue = ReplaceValue(RuleValue, parameter_ids=(ParameterValue.id,))
            Parameters.append(ParameterValue)
        Entities.extend(Picks)
        Rules.append(RuleValue)
    return tuple(Entities), tuple(Rules), tuple(Parameters)
