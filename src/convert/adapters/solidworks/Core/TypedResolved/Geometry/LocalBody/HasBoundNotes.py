from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import ReadNodeName
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import KResolvedFeaturesStream
from convert.adapters.solidworks.Core.Native import NativeFeature
from convert.adapters.solidworks.Core.Preparation.ThroughAll.Members.ReadNotesInput import (
    ReadNotesInput,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.Presentation.CheckTreeAlias import (
    CheckTreeAlias,
)
from convert.adapters.solidworks.Core.TypedResolved.Presentation.ReadChildren import (
    ReadChildren,
)
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink


# anonymous end tags qualify as scaffold only through the actual reciprocal note pair
def HasBoundNotes(
    Archive: SldprtArchive, NotesValue: tuple[NativeFeature, ...]
) -> bool:
    if len(NotesValue) != 2 or any(
        ItemValue.xml_tag != "Feature"
        or ItemValue.native_stream != KResolvedFeaturesStream
        or ItemValue.class_name not in ("", "moNotesAreaFtrFolder_c")
        for ItemValue in NotesValue
    ):
        return False
    try:
        LinkValue = ReadNativeLink(Archive, 0)
        (Cabinet,) = (
            NodeValue
            for NodeValue in LinkValue.ResolvedValue.RootsValue
            if NodeValue is not None
            and NodeValue.ClassValue.NameValue == "moDetailCabinet_c"
        )
        NodesValue = ReadChildren(Cabinet)
        CheckTreeAlias(LinkValue, (Cabinet, *NodesValue))
        _ = ReadNotesInput(NodesValue)
        Actual = {
            (NativeNodeId(NodeValue), ReadNodeName(NodeValue)): NodeValue
            for NodeValue in NodesValue
        }
        for ItemValue in NotesValue:
            NodeValue = Actual.pop((ItemValue.object_id, ItemValue.name))
            if (
                ItemValue.native_offset is None
                or NodeValue.StartOffset is None
                or NodeValue.EndOffset is None
                or not NodeValue.StartOffset
                <= ItemValue.native_offset
                < NodeValue.EndOffset
            ):
                return False
    except (KeyError, TypeError, ValueError):
        return False
    return not Actual
