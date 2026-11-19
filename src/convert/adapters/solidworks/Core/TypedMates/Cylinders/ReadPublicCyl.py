from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Mates.MatesGraph import MatesGraph
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedMates.PublicMateEnv import PublicMateEnv
from convert.adapters.solidworks.Core.TypedMates.CheckMateIds import CheckMateIds
from convert.adapters.solidworks.Core.TypedMates.Cylinders.CheckCylIds import (
    CheckCylIds,
)
from convert.adapters.solidworks.Core.TypedMates.ReadFixedFlags import ReadFixedFlags
from convert.adapters.solidworks.Core.TypedMates.Cylinders.CheckCylMode import (
    CheckCylMode,
)
from convert.adapters.solidworks.Core.TypedMates.Cylinders.CheckCylRefs import (
    CheckCylRefs,
)
from convert.adapters.solidworks.Core.TypedMates.Cylinders.MakeCylContext import (
    MakeCylContext,
)
from convert.adapters.solidworks.Core.TypedMates.Cylinders.ReadCylChild import (
    ReadCylChild,
)
from convert.adapters.solidworks.Core.TypedMates.Cylinders.ReadCylRows import (
    ReadCylRows,
)
from interchange import MateConstraint, MateEntity


# the public cylinder route must bind complete linked records to the already resolved real child before replacing legacy semantics
def ReadPublicCyl(
    EnvValue: PublicMateEnv,
    LinkValue: NativeLink,
    GraphValue: MatesGraph,
    LegacyEntities: tuple[MateEntity, ...],
    LegacyRules: tuple[MateConstraint, ...],
) -> tuple[tuple[MateEntity, ...], tuple[MateConstraint, ...], Mapping[str, object]]:
    Context = MakeCylContext(EnvValue, LinkValue)
    (NodeValue,) = GraphValue.RootsValue
    CheckCylMode(NodeValue)
    CheckMateIds(GraphValue.RootsValue, LinkValue)
    CheckCylIds(NodeValue)
    CheckCylRefs(NodeValue, Context.ModelNode, LinkValue.ConfigValue.HeaderValue)
    ItemValue = next(iter(Context.OccurrenceMap.values()))
    ChildValue = ReadCylChild(
        EnvValue.PathsValue[ItemValue.definition_id],
        EnvValue.DocumentsValue[ItemValue.definition_id],
        ItemValue.configuration_name,
    )
    Entities, RuleValue = ReadCylRows(
        NodeValue, Context, ChildValue, LegacyEntities, LegacyRules[0]
    )
    return (
        Entities,
        (RuleValue,),
        {
            "status": "admitted",
            "scope": "ordinary_concentric_single_mate_two_direct_part_occurrences",
            "archive_version": 19000,
            "mate_count": 1,
            "map_base": GraphValue.MapBase,
            "map_terminal": GraphValue.MapValue.CounterValue,
            "typed_occurrence_and_child_surface_identity": True,
            "occurrence_fixed_flags": ReadFixedFlags(Context),
            "full_selected_mate_graph": True,
            "public_writer_qualified": False,
            "grammar_coverage": dict(GraphValue.ReportValue),
        },
    )
