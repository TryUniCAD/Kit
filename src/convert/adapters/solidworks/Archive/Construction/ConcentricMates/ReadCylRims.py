from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Partition.ReadXmtVector import ReadXmtVector
from convert.adapters.solidworks.Archive.Partition.RequireXmt import RequireXmt
from convert.adapters.solidworks.Archive.Partition.WalkXmtChain import WalkXmtChain
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from convert.adapters.solidworks.Core.TypedMates.Cylinders.ReadCylWords import (
    ReadCylWords,
)


# each rim must follow the two actual half edges to its own circular edge and cap
def ReadCylRims(
    NodesValue: Mapping[int, XmtNode],
    FaceValue: XmtNode,
    Carrier: XmtNode,
    FeatureId: int,
    EpochValue: int,
) -> tuple[
    tuple[tuple[float, float, float], tuple[float, float, float]],
    tuple[tuple[int, int], tuple[int, int]],
]:
    LoopsValue = WalkXmtChain(
        NodesValue,
        FaceValue.Integer("loop"),
        15,
        PreviousField=None,
        OwnerField="face",
        OwnerValue=FaceValue.IndexValue,
    )
    if len(LoopsValue) != 2:
        raise ValueError("generated cylinder requires its two actual lateral rims")
    Centres: list[tuple[float, float, float]] = []
    Selectors: list[tuple[int, int]] = []
    for IndexValue in LoopsValue:
        LoopValue = NodesValue[IndexValue]
        FinValue = RequireXmt(NodesValue, LoopValue.Integer("halfedge"), 17)
        Other = RequireXmt(NodesValue, FinValue.Integer("other"), 17)
        CapLoop = RequireXmt(NodesValue, Other.Integer("loop"), 15)
        CapValue = RequireXmt(NodesValue, CapLoop.Integer("face"), 14)
        PlaneValue = RequireXmt(NodesValue, CapValue.Integer("surface"), 50)
        EdgeValue = RequireXmt(NodesValue, FinValue.Integer("edge"), 16)
        Circle = RequireXmt(NodesValue, EdgeValue.Integer("curve"), 31)
        WordsValue = ReadCylWords(NodesValue, CapValue)
        Centre = ReadXmtVector(Circle, "centre")
        if (
            len(WordsValue) != 6
            or WordsValue[:4] != (40, FeatureId, EpochValue, 0)
            or PlaneValue.Integer("owner") != CapValue.IndexValue
            or ReadXmtVector(PlaneValue, "pvec") != Centre
            or ReadXmtVector(Circle, "normal") != ReadXmtVector(Carrier, "axis")
            or RequireScalar(Circle.FieldsValue.get("radius"))
            != Carrier.FieldsValue["radius"]
        ):
            raise ValueError("selected circle rim lacks its actual coaxial cap owner")
        Centres.append(Centre)
        Selectors.append((WordsValue[4], WordsValue[5]))
    if Selectors != [(1, 0), (0, 0)]:
        raise ValueError("generated cylinder has unrepresented cap order")
    return (Centres[0], Centres[1]), (Selectors[0], Selectors[1])
