from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Mates.ReadMatesMut import ReadMatesMut
from convert.adapters.solidworks.Archive.Mates.WriteMatesMut import WriteMatesMut
from convert.adapters.solidworks.Assembly.PlanarMates.PlanarContext import PlanarContext
from convert.adapters.solidworks.Core.TypedMates.PublicMateEnv import PublicMateEnv
from convert.adapters.solidworks.Core.TypedMates.CheckMateIds import CheckMateIds
from convert.adapters.solidworks.Core.TypedMates.ReadMateKids import ReadMateKids
from convert.adapters.solidworks.Core.TypedMates.ReadPublicMate import ReadPublicMate
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from interchange import MateConstraint, MateEntity


# public typed mates require the complete linked stream and independently loaded child configurations
def ReadPublicMates(
    EnvValue: PublicMateEnv,
    LegacyEntities: tuple[MateEntity, ...],
    LegacyRules: tuple[MateConstraint, ...],
) -> tuple[tuple[MateEntity, ...], tuple[MateConstraint, ...], Mapping[str, object]]:
    LinkValue = ReadNativeLink(EnvValue.ArchiveValue, 0)
    BufferValue = EnvValue.ArchiveValue.require("Contents/Config-0-MatesList")
    GraphValue = ReadMatesMut(BufferValue, LinkValue.ResolvedValue)
    Encoded, _ = WriteMatesMut(GraphValue.RootsValue, LinkValue.ResolvedValue)
    if (
        Encoded != BufferValue
        or len(GraphValue.RootsValue) != 1
        or len(LegacyRules) != 1
    ):
        raise ValueError("typed mate stream bytes or complete inventory differ")
    Native = EnvValue.NativeValue
    Items = {Value.feature_id: Value for Value in Native.occurrences}
    if len(Items) != len(Native.occurrences):
        raise ValueError("typed mate occurrence feature ids are ambiguous")
    Context = PlanarContext(
        LinkValue.ConfigValue.RootValue,
        Items,
        {Value.object_id: Value for Value in Native.definitions},
        ReadMateKids(EnvValue),
    )
    CheckMateIds(GraphValue.RootsValue[0], LinkValue)
    Entities, RuleValue = ReadPublicMate(
        GraphValue.RootsValue[0],
        Context,
        EnvValue,
        LegacyRules[0],
        {Value.id: Value for Value in LegacyEntities},
    )
    return (
        Entities,
        (RuleValue,),
        {
            "status": "admitted",
            "scope": "ordinary_aligned_single_mate_two_direct_part_occurrences",
            "archive_version": 19000,
            "mate_count": 1,
            "map_base": GraphValue.MapBase,
            "map_terminal": GraphValue.MapValue.CounterValue,
            "typed_occurrence_and_child_datum_identity": True,
            "full_selected_mate_graph": True,
            "public_writer_qualified": False,
            "grammar_coverage": dict(GraphValue.ReportValue),
        },
    )
