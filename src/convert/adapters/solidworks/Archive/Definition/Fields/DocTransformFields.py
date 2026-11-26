from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Definition.Fields.ScalarFields import (
    MakeScalarRows,
)

# perspective and matrix variants follow the mode carried by each stored transform
KDocTransformFields = MappingProxyType(
    {
        "mgMatrix5_c.restore": (
            NativeField("Scalar", "dim", "i32"),
            *(NativeField("Scalar", f"m{Index}", "f64") for Index in range(25)),
        ),
        "mgPerspInfoBase_c.restore": MakeScalarRows("f64", "f08 f10 f18 f20"),
        "mgPerspInfo_c.restore": MakeScalarRows("f64", "f08 f10 f18 f20 f28 f30"),
    }
)
