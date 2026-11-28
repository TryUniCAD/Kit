from convert.adapters.solidworks.Archive.Construction.PlanarMates.DatumTime import (
    DatumTime,
)
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import FieldInt
from convert.adapters.solidworks.Core.TypedMates.Cylinders.CylChild import CylChild
from convert.adapters.solidworks.Core.TypedMates.Cylinders.ReadCylWords import (
    ReadCylWords,
)


# matching geometry alone cannot replace the actual feature epoch and sketch permanent marker identity
def CheckCylSide(ChildValue: CylChild) -> None:
    FeatureId = FieldInt(ChildValue.FeatureValue.FieldsValue, "f08")
    CreationTime = DatumTime(ChildValue.LinkValue.ConfigValue.HeaderValue, FeatureId)
    Expected = (74, FeatureId, CreationTime, 0, ChildValue.ArcMarker)
    if ReadCylWords(ChildValue.NodesValue, ChildValue.FaceValue) != Expected:
        raise ValueError(
            "concentric lateral identity differs from its actual extrusion and arc"
        )
