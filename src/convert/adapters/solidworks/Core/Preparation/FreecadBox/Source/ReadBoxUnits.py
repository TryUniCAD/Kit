from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Construction.Units.UnitInput import UnitInput
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.ReadEnumText import (
    ReadEnumText,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.SourceProperty import (
    ReadPropText,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.SourceFields import (
    RequireBox,
)


# native units come from the document selector and require the measured empty string map
def ReadBoxUnits(
    SourceValue: Mapping[str, object],
    Properties: Mapping[str, object],
) -> tuple[UnitInput, dict[str, str]]:
    RequireBox(
        SourceValue["string_hasher"]
        == {
            "attribute": "1",
            "entries": [],
            "nodes": [
                {
                    "attributes": {"count": "0", "saveall": "0", "threshold": "0"},
                    "tag": "StringHasher",
                }
            ],
        },
        "FreeCAD document has a populated string map",
    )
    NameValue = ReadEnumText(Properties, "UnitSystem")
    Hasher = ReadPropText(Properties, "UseHasher", "Bool", "Bool")
    RequireBox(
        NameValue == "Standard (mm, kg, s, °)" and Hasher == "true",
        "FreeCAD box has an unqualified document unit or string hasher mode",
    )
    return UnitInput("mm", "degree", "custom", 4, "kg"), {
        "FreeCAD Unit System": NameValue,
        "FreeCAD Use Hasher": Hasher,
    }
