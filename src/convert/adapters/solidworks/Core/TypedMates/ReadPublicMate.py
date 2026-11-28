from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.PlanarContext import PlanarContext
from convert.adapters.solidworks.Assembly.PlanarMates.ReadPlanarMate import (
    ReadPlanarMate,
)
from convert.adapters.solidworks.Core.TypedMates.CheckMateDatum import CheckMateDatum
from convert.adapters.solidworks.Core.TypedMates.CheckMateMode import CheckMateMode
from convert.adapters.solidworks.Core.TypedMates.CheckMatePoint import CheckMatePoint
from convert.adapters.solidworks.Core.TypedMates.CheckPerpMate import CheckPerpMate
from convert.adapters.solidworks.Core.TypedMates.MakeMateEntity import MakeMateEntity
from convert.adapters.solidworks.Core.TypedMates.MakeMateRule import MakeMateRule
from convert.adapters.solidworks.Core.TypedMates.MateProvenance import MateProvenance
from convert.adapters.solidworks.Core.TypedMates.PublicMateEnv import PublicMateEnv
from interchange import MateConstraint, MateEntity


# a public replacement is complete only when every endpoint and live mate input passes its own guard
def ReadPublicMate(
    NodeValue: ArchiveNode,
    Context: PlanarContext,
    EnvValue: PublicMateEnv,
    LegacyRule: MateConstraint,
    LegacyEntities: Mapping[str, MateEntity],
) -> tuple[tuple[MateEntity, ...], MateConstraint]:
    CheckMateMode(NodeValue)
    PlanValue = ReadPlanarMate(Context, NodeValue, 19000)
    if PlanValue.NameValue != LegacyRule.name or PlanValue.KindValue != str(
        LegacyRule.kind
    ):
        raise ValueError("typed mate and legacy inventory differ in name or class")
    for Endpoint in PlanValue.Endpoints:
        CheckMateDatum(Endpoint, EnvValue)
        CheckMatePoint(Endpoint, Context)
    CheckPerpMate(PlanValue, NodeValue, Context, ColdValue=EnvValue.ColdPerp)
    ProvenanceValue = MateProvenance(NodeValue)
    Entities = tuple(
        MakeMateEntity(Value, LegacyRule, Index, ProvenanceValue, LegacyEntities)
        for Index, Value in enumerate(PlanValue.Endpoints)
    )
    return Entities, MakeMateRule(
        PlanValue, NodeValue, LegacyRule, Entities, ProvenanceValue
    )
