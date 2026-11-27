from convert.Formats.Fusion.BrepCodec.Journal.Geometry.JournalVector import (
    KJournalVector,
)
from convert.Geometry.Revolve.SweepVector import DotVector
from interchange.geometry.Models.Transform import Transform
from interchange.geometry.Models.VectorSpace import SpaceVector


# directions must rotate without the translation applied to native world points
def LocalDualVector(Value: KJournalVector, Frame: Transform) -> KJournalVector:
    Vector = SpaceVector(*Value)
    return (
        DotVector(Vector, Frame.x_axis),
        DotVector(Vector, Frame.y_axis),
        DotVector(Vector, Frame.z_axis),
    )
