from collections.abc import Mapping

from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.SourceFields import (
    ReadBoxString,
    RequireBox,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.SourceSchema import (
    KDefaultMat,
)


# an assigned material outside the measured library default needs a different projection
def ReadBoxMat(Properties: Mapping[str, object]) -> str:
    RecordValue = NativeRecord(Properties["ShapeMaterial"])
    RequireBox(
        RecordValue["tag"] == "Property"
        and NativeRecord(RecordValue["attributes"])["type"]
        == "Materials::PropertyMaterial",
        "FreeCAD shape material has another property type",
    )
    (Material,) = NativeRows(RecordValue["children"])
    Attributes = NativeRecord(Material["attributes"])
    RequireBox(
        Material["tag"] == "PropertyMaterial"
        and Attributes == {"uuid": KDefaultMat}
        and not Material.get("children"),
        "FreeCAD box uses an unqualified material assignment",
    )
    return ReadBoxString(Attributes["uuid"])
