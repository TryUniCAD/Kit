from convert.adapters.solidworks.Archive.Partition.LocalPrism.CheckPrismRings import (
    PrismRings,
)
from convert.adapters.solidworks.Archive.Partition.LocalPrism.ReadPrismFaces import (
    ReadPrismFaces,
)
from convert.Geometry.Parasolid import BrepTopology
from interchange.brep.Topology.BrepModel import BrepModel


# a qualified six sided section has one reflex corner in its actual lower face loop
def CheckLPrism(ModelValue: BrepModel) -> None:
    TopologyValue = BrepTopology(ModelValue)
    RingsValue = PrismRings(ReadPrismFaces(ModelValue, TopologyValue), TopologyValue)
    Lower = min(Value.point.z for Value in ModelValue.vertices)
    CapsValue = tuple(
        RingValue
        for RingValue in RingsValue
        if all(PointValue[2] == Lower for PointValue in RingValue)
    )
    if len(CapsValue) != 1 or len(CapsValue[0]) != 6:
        raise ValueError("local concave solid needs one six corner lower section")
    (RingValue,) = CapsValue
    Vectors = tuple(
        (EndPoint[0] - StartPoint[0], EndPoint[1] - StartPoint[1])
        for StartPoint, EndPoint in zip(
            RingValue, RingValue[1:] + RingValue[:1], strict=True
        )
    )
    Turns = tuple(
        First[0] * Second[1] - First[1] * Second[0]
        for First, Second in zip(Vectors, Vectors[1:] + Vectors[:1], strict=True)
    )
    if (
        any((XValue == 0) == (YValue == 0) for XValue, YValue in Vectors)
        or any(TurnValue == 0 for TurnValue in Turns)
        or sum(TurnValue > 0 for TurnValue in Turns) not in (1, 5)
    ):
        raise ValueError("local concave solid requires one orthogonal reflex corner")
