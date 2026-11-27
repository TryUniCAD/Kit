from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Mates.ReadMatesMut import ReadMatesMut
from convert.adapters.solidworks.Archive.Mates.WriteMatesMut import WriteMatesMut
from convert.adapters.solidworks.Assembly.PlanarMates.PlanarContext import PlanarContext
from convert.adapters.solidworks.Core.TypedMates.CheckColdGroup import CheckColdGroup
from convert.adapters.solidworks.Core.TypedMates.ColdMateLayout import (
    KColdMateClasses,
    KColdMateScope,
)
from convert.adapters.solidworks.Core.TypedMates.PublicMateEnv import PublicMateEnv
from convert.adapters.solidworks.Core.TypedMates.CheckMateIds import CheckMateIds
from convert.adapters.solidworks.Core.TypedMates.CheckMateWrappers import (
    CheckMateWraps,
)
from convert.adapters.solidworks.Core.TypedMates.ReadMateKids import ReadMateKids
from convert.adapters.solidworks.Core.TypedMates.ReadMateGroup import ReadMateGroup
from convert.adapters.solidworks.Core.TypedMates.ReadMateRows import ReadMateRows
from convert.adapters.solidworks.Core.TypedMates.ReadFixedFlags import ReadFixedFlags
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from interchange import MateConstraint, MateEntity, MateGroup, Parameter


# public typed mates require the complete linked stream and independently loaded child configurations
def ReadPublicMates(
    EnvValue: PublicMateEnv,
    LegacyEntities: tuple[MateEntity, ...],
    LegacyRules: tuple[MateConstraint, ...],
    LegacyGroups: tuple[MateGroup, ...],
    *,
    Deferred: bool = False,
) -> tuple[
    tuple[MateEntity, ...],
    tuple[MateConstraint, ...],
    tuple[MateGroup, ...],
    tuple[Parameter, ...],
    Mapping[str, object],
]:
    LinkValue = ReadNativeLink(EnvValue.ArchiveValue, 0, AssemblyValue=True)
    BufferValue = EnvValue.ArchiveValue.require("Contents/Config-0-MatesList")
    GraphValue = ReadMatesMut(BufferValue, LinkValue.ResolvedValue)
    Encoded, _ = WriteMatesMut(GraphValue.RootsValue, LinkValue.ResolvedValue)
    if (
        Encoded != BufferValue
        or not GraphValue.RootsValue
        or len(GraphValue.RootsValue) != len(LegacyRules)
    ):
        raise ValueError("typed mate stream bytes or complete inventory differ")
    IsColdTriple = len(GraphValue.RootsValue) == len(KColdMateClasses)
    CheckMateIds(GraphValue.RootsValue, LinkValue)
    CheckMateWraps(GraphValue.RootsValue)
    if LegacyGroups:
        raise ValueError("ordinary planar mates have additional legacy group owners")
    Native = EnvValue.NativeValue
    Items = {Value.feature_id: Value for Value in Native.occurrences}
    if len(Items) != len(Native.occurrences):
        raise ValueError("typed mate occurrence feature ids are ambiguous")
    Context = PlanarContext(
        LinkValue.ConfigValue.RootValue,
        Items,
        {Value.object_id: Value for Value in Native.definitions},
        {} if Deferred else ReadMateKids(EnvValue, ColdRequired=IsColdTriple),
    )
    Entities, Rules, Parameters = ReadMateRows(
        GraphValue.RootsValue,
        Context,
        EnvValue,
        LegacyRules,
        LegacyEntities,
        Deferred=Deferred,
    )
    GroupValue = ReadMateGroup(
        LinkValue, GraphValue, Rules, LegacyRules[0].owner_definition_id
    )
    if Deferred:
        return (
            Entities,
            Rules,
            (GroupValue,),
            Parameters,
            {
                "status": "deferred",
                "full_selected_mate_graph": False,
                "public_writer_qualified": False,
            },
        )
    FixedFlags = ReadFixedFlags(Context)
    if IsColdTriple:
        CheckColdGroup(GraphValue.RootsValue, Rules, Parameters, FixedFlags)
    return (
        Entities,
        Rules,
        (GroupValue,),
        Parameters,
        {
            "status": "admitted",
            "scope": (
                KColdMateScope
                if IsColdTriple
                else "ordinary_aligned_mates_direct_part_occurrences"
            ),
            "archive_version": 19000,
            "mate_count": len(Rules),
            "map_base": GraphValue.MapBase,
            "map_terminal": GraphValue.MapValue.CounterValue,
            "typed_occurrence_and_child_datum_identity": True,
            "occurrence_fixed_flags": FixedFlags,
            "full_selected_mate_graph": True,
            "public_writer_qualified": False,
            "grammar_coverage": dict(GraphValue.ReportValue),
        },
    )
