from convert.adapters.solidworks.Archive.Construction.PlanarMates.DatumTime import (
    DatumTime,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative
from convert.adapters.solidworks.Core.TypedResolved.Revolves.SelectedCut.CheckRevBands import (
    CheckRevBands,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.SelectedCut.CheckRevResult import (
    CheckRevResult,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.SelectedCut.CheckRevSelf import (
    CheckRevSelf,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.SelectedCut.CheckRevStock import (
    CheckRevStock,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.SelectedCut.ReadRevBand import (
    ReadRevBand,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.SelectedCut.ReadRevChoices import (
    ReadRevChoices,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.SelectedCut.ReadRevFace import (
    ReadRevFace,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.SelectedCut.RevCutLineage import (
    RevCutLineage,
)


# the actual selected face and both output choosers must corroborate the same consumed stock
def CheckRevPick(
    LinkValue: NativeLink, TopHeader: ArchiveNode, Lineage: RevCutLineage
) -> None:
    First, Second = Lineage.StockValues
    CutValue = Lineage.CutValue
    FirstBand, SecondBand, CutBand = (
        ReadRevBand(Value) for Value in (First, Second, CutValue)
    )
    CheckRevBands(FirstBand, SecondBand, CutBand)
    FirstId, SecondId, CutId = (
        NativeNodeId(Value.NodeValue) for Value in (First, Second, CutValue)
    )
    Header = LinkValue.ConfigValue.HeaderValue
    Epochs = {
        FeatureId: DatumTime(Header, FeatureId)
        for FeatureId in (FirstId, SecondId, CutId)
    }
    if any(
        Value == 2592000 or DatumTime(TopHeader, FeatureId) != Value
        for FeatureId, Value in Epochs.items()
    ):
        raise ValueError("selected revolve cut requires matching saved creation events")
    Selection = RequireNative(
        Lineage.WrapperValue.FieldsValue.get("ff0"), "moFaceRef_c"
    )
    Faces = ReadRevFace(LinkValue, Selection, Epochs, 5, 0x200)
    Index = Lineage.AtomsValue.SelectedIndex
    SelectedId, StockBand = ((FirstId, FirstBand), (SecondId, SecondBand))[Index]
    Marks = {Value.MarkValue for Value in Faces}
    if (
        len(Marks) != 3
        or not Marks <= StockBand.Marks
        or any(Value.IsEnd or Value.FeatureId != SelectedId for Value in Faces)
    ):
        raise ValueError(
            "revolve cut selector face does not resolve to its consumed producer"
        )
    FirstFaces, SecondFaces, CutFaces = (
        ReadRevChoices(LinkValue, Value.NodeValue, Epochs, CountValue)
        for Value, CountValue in ((First, 5), (Second, 5), (CutValue, 6))
    )
    CheckRevStock(FirstFaces, FirstId, FirstBand)
    CheckRevStock(SecondFaces, SecondId, SecondBand)
    CheckRevResult(
        CutFaces,
        SelectedId,
        CutId,
        StockBand.Walls[1 - Index],
        CutBand.Marks - {CutBand.Walls[1 - Index]},
    )
    CheckRevSelf(
        Header,
        (
            *Faces,
            *FirstFaces[0],
            *FirstFaces[1],
            *SecondFaces[0],
            *SecondFaces[1],
            *CutFaces[0],
            *CutFaces[1],
        ),
    )
