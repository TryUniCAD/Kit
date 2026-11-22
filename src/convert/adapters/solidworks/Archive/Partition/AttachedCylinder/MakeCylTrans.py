from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Archive.Partition.AttachedCylinder.Attributes.BodyTrackIn import (
    BodyTrackIn,
)
from convert.adapters.solidworks.Archive.Partition.AttachedCylinder.Attributes.CylAttrIntents import (
    CylAttrIntents,
)
from convert.adapters.solidworks.Archive.Partition.AttachedCylinder.Attributes.MakeCylAttrs import (
    MakeCylAttrs,
)
from convert.adapters.solidworks.Archive.Partition.AttachedCylinder.Attributes.MakeCylTags import (
    MakeCylTags,
)
from convert.adapters.solidworks.Archive.Partition.AttachedCylinder.CylPartition import (
    CylPartition,
)
from convert.adapters.solidworks.Archive.Partition.AttachedCylinder.Geometry.CylSpan import (
    CylSpan,
)
from convert.adapters.solidworks.Archive.Partition.AttachedCylinder.Geometry.MakeCylBoundary import (
    MakeCylBoundary,
)
from convert.adapters.solidworks.Archive.Partition.AttachedCylinder.MakeCylMarks import (
    MakeCylMarks,
)
from convert.adapters.solidworks.Archive.Partition.AttachedCylinder.WriteCylHist import (
    WriteCylHist,
)
from convert.adapters.solidworks.Archive.Partition.CheckXmtAttrs import CheckXmtAttrs
from convert.adapters.solidworks.Archive.Partition.CheckXmtGraph import CheckXmtGraph
from convert.adapters.solidworks.Archive.Partition.CheckXmtMarks import CheckXmtMarks
from convert.adapters.solidworks.Archive.Partition.ImportHistory.MakeEmptyWorld import (
    MakeEmptyWorld,
)


# the attached cylinder active graph and persistent attributes and rollback share one allocation
def MakeCylTrans(SpanValue: CylSpan, TrackValue: BodyTrackIn) -> CylPartition:
    BodyValue, NodesValue, FacesValue = MakeCylBoundary(SpanValue)
    TagsValue = MakeCylTags(NodesValue)
    IntentsValue = CylAttrIntents(BodyValue, FacesValue, TagsValue, TrackValue)
    WorldValue = MakeEmptyWorld(1, 1, 0)
    ActiveValue, PointerSlots = MakeCylAttrs(
        WorldValue, BodyValue, NodesValue, IntentsValue
    )
    JournalValue = MakeCylMarks(ActiveValue, PointerSlots)
    SelectedId = JournalValue.SelectedValue.Integer("id")
    ActivationId = JournalValue.ActivationValue.Integer("id")
    ActiveValue = (
        ReplaceValue(
            ActiveValue[0],
            FieldsValue=dict(ActiveValue[0].FieldsValue)
            | {
                "current_id": SelectedId,
                "highest_id": SelectedId,
                "body": BodyValue.IndexValue,
            },
        ),
        *ActiveValue[1:],
    )
    ActiveMap = {NodeValue.IndexValue: NodeValue for NodeValue in ActiveValue}
    CheckXmtGraph(ActiveMap)
    CheckXmtAttrs(ActiveMap, ActiveMap[BodyValue.IndexValue])
    CheckXmtMarks(
        ActiveMap,
        JournalValue.RootValue,
        {
            NodeValue.IndexValue: NodeValue
            for NodeValue in (
                JournalValue.InitialValue,
                JournalValue.ActivationValue,
                JournalValue.SelectedValue,
            )
        },
        {
            JournalValue.SelectedValue.IndexValue: frozenset(
                NodeValue.IndexValue for NodeValue in JournalValue.RemovedValues
            ),
            JournalValue.ActivationValue.IndexValue: frozenset(),
        },
    )
    return CylPartition(
        WriteCylHist(ActiveValue, JournalValue),
        TagsValue[BodyValue.IndexValue],
        TagsValue[FacesValue[-1].IndexValue],
        ActivationId,
        SelectedId,
    )
