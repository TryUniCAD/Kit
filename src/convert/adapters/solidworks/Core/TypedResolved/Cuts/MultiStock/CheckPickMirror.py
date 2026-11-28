from convert.adapters.solidworks.Core.TypedResolved.Circles.ReadLocalCirc import (
    ReadLocalCirc,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.ReadChooserPair import (
    ReadChooserPair,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.ReadCutFace import (
    ReadCutFace,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.ReadStockRef import (
    ReadStockRef,
)
from convert.adapters.solidworks.Core.TypedResolved.ExtrudeOwner import ExtrudeOwner
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.Presentation.ReadThruStock import (
    ReadThruStock,
)
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# a saved selection without a face needs both cut choosers to repeat the same mapped stock and cut representation links
def CheckPickMirror(
    LinkValue: NativeLink, StockValue: ExtrudeOwner, CutValue: ExtrudeOwner
) -> None:
    StockNode, CutNode = StockValue.NodeValue, CutValue.NodeValue
    StockFaces = ReadChooserPair(LinkValue, StockNode, "f4a8")
    FirstRef, SecondRef = (
        ReadStockRef(FaceValue, StockNode, 4, LinkValue=LinkValue)
        for FaceValue in StockFaces
    )
    if FirstRef is not SecondRef:
        raise ValueError("selected stock chooser faces have different external owners")
    LineMarks = frozenset(
        Value.PermanentId
        for Value in ReadThruStock(StockValue.ProfileValue, LinkValue).LinesValue
    )
    Sketch = RequireNative(CutValue.ProfileValue.FieldsValue.get("pd_f80"), "sgSketch")
    Circle = ReadLocalCirc(Sketch, LinkValue, AllowFree=True)
    if len(LineMarks) != 4 or Circle is None or Circle[1] is not None:
        raise ValueError("saved stock chooser has alternate stock or cut sketches")
    Primary = ReadChooserPair(LinkValue, CutNode, "f4a8")
    Mirror = ReadChooserPair(LinkValue, CutNode, "f4c0")
    if len(set((*Primary, *Mirror))) != 4:
        raise ValueError("saved cut choosers do not own distinct face carriers")
    OwnerIds = (NativeNodeId(StockNode), NativeNodeId(CutNode))
    PrimaryReps, MirrorReps = (
        tuple(
            ReadCutFace(
                LinkValue, FaceValue, FirstRef, OwnerIds, LineMarks, Circle[0].ArcMark
            )
            for FaceValue in FacePair
        )
        for FacePair in (Primary, Mirror)
    )
    if PrimaryReps != MirrorReps:
        raise ValueError(
            "saved cut choosers do not mirror actual representation identities"
        )
