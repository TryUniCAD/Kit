from convert.adapters.Fusion.Native.Graph.GraphValues import (
    CheckIdentity,
    ObjectFields,
    PointCoords,
)
from convert.adapters.Fusion.Native.Graph.NativeNode import NativeNode
from convert.Formats.Fusion.EntityCodec.Model.MatrixValue import MatrixValue
from interchange.geometry.Models.Transform import Transform
from interchange.geometry.Models.VectorSpace import SpaceVector


# native sketch axes differ from datum axes and must retain the saved principal basis
def ReadFrameBasis(
    PlaneNode: NativeNode, Matrix: NativeNode, Datum: NativeNode
) -> Transform:
    Saved = PlaneNode.Fields["transform"]
    if not isinstance(Saved, MatrixValue) or Matrix.Fields["matrix3d"] != Saved:
        raise ValueError(
            "Native dual frame coordinate and definition matrices disagree"
        )
    Plane = ObjectFields(Datum.Fields["plane"])
    Origin = PointCoords(Plane["origin"])
    AxisU, AxisV = PointCoords(Plane["uAxis"]), PointCoords(Plane["vAxis"])
    IsXzPlane = Datum.Fields["originName"] == "XZ"
    if (
        Plane["normalReversed"] is not False
        or Origin != (0.0, 0.0, 0.0)
        or AxisU != ((0.0, 0.0, 1.0) if IsXzPlane else (1.0, 0.0, 0.0))
        or AxisV != ((1.0, 0.0, 0.0) if IsXzPlane else (0.0, 1.0, 0.0))
    ):
        raise ValueError("Native dual frame datum has an unsupported principal basis")
    AxisX = AxisV if IsXzPlane else AxisU
    AxisY = tuple(-Value for Value in AxisU) if IsXzPlane else AxisV
    AxisZ = tuple(
        AxisX[(Index + 1) % 3] * AxisY[(Index + 2) % 3]
        - AxisX[(Index + 2) % 3] * AxisY[(Index + 1) % 3]
        for Index in range(3)
    )
    Expected = tuple(
        Value
        for Index in range(3)
        for Value in (AxisX[Index], AxisY[Index], AxisZ[Index], Origin[Index])
    ) + (0.0, 0.0, 0.0, 1.0)
    Values = (
        Saved.Entries
        if Saved.Entries is not None
        else tuple(float(First == Second) for First in range(4) for Second in range(4))
    )
    if Values != Expected:
        raise ValueError(
            "Native dual frame differs from the selected default sketch basis"
        )
    return Transform(
        SpaceVector(*(Value * 10 for Value in Origin)),
        SpaceVector(*AxisX),
        SpaceVector(*AxisY),
        SpaceVector(*AxisZ),
    )
