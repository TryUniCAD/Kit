from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.Patterns.PatternBaseFields import (
    KPatternBaseFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.Patterns.PatternOrigFields import (
    KPatternOrigFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.Patterns.PatternShapeFields import (
    KPatternShapeFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.Patterns.PatternTailFields import (
    KPatternTailFields,
)
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# each shared pattern body keeps the field rules of its actual native owner
KPatternFields = MappingProxyType(
    {
        "moLPattern_c": KPatternTailFields,
        "moPattern_c.FUN_4bb1aa00": KPatternBaseFields,
        "moShapePatternData_c.FUN_4bb1ed50": KPatternShapeFields,
        "moOrigDimData_c.Serialize": KPatternOrigFields,
        "rf.su_CMapObToInt": (
            NativeField(
                "Array",
                "items",
                "Count",
                BodyValue=(NativeField("Node", "k"), NativeField("Scalar", "v", "i32")),
                CountValue="n",
            ),
        ),
    }
)
