from collections.abc import Mapping

from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.CheckIdentity import (
    CheckIdentity,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.ReadBoxMat import (
    ReadBoxMat,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.SourceProperty import (
    ReadPropChild,
    ReadPropText,
    RequireEmpty,
    RequireProp,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.SourceFields import (
    RequireBox,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.SourceSchema import (
    KBodyProps,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.NativeRows import NativeRows


# a body must own exactly the projected primitive and the actual origin group
def CheckBoxBody(
    Properties: Mapping[str, object], BodyName: str, PartName: str, Release: str
) -> dict[str, str]:
    Expected = (
        KBodyProps
        if Release == "0.21"
        else KBodyProps | {"AllowCompound", "ShapeMaterial"}
    )
    RequireBox(frozenset(Properties) == Expected, "FreeCAD Body property set differs")
    CheckIdentity(Properties, "Placement")
    RequireProp(Properties, "BaseFeature", "Link", "Link", "")
    RequireProp(Properties, "Label", "String", "String", BodyName)
    RequireProp(Properties, "Label2", "String", "String", "")
    RequireProp(Properties, "Visibility", "Bool", "Bool", "true")
    RequireEmpty(Properties, "ExpressionEngine", "ExpressionEngine", "ExpressionEngine")
    RequireProp(Properties, "Tip", "Link", "Link", PartName)
    RequireProp(Properties, "Origin", "Link", "Link", "Origin")
    Links = ReadPropChild(Properties["Group"], "LinkList", "LinkList")
    Children = NativeRows(Links["children"])
    RequireBox(
        NativeRecord(Links["attributes"])["count"] == "1"
        and len(Children) == 1
        and Children[0]["tag"] == "Link"
        and NativeRecord(Children[0]["attributes"])["value"] == PartName,
        "FreeCAD Body group owns another source feature",
    )
    if Release == "0.21":
        return {}
    Compound = ReadPropText(Properties, "AllowCompound", "Bool", "Bool")
    RequireBox(
        Compound in ("false", "true"), "FreeCAD Body has a malformed compound setting"
    )
    return {
        "FreeCAD Body Allows Compound": Compound,
        "FreeCAD Body Material UUID": ReadBoxMat(Properties),
    }
