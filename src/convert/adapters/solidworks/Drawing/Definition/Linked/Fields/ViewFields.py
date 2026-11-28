from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Definition.Fields.ScalarFields import (
    MakeScalarRows,
)
from convert.adapters.solidworks.Drawing.Definition.Linked.Fields.ViewLead import (
    KViewLead,
)
from convert.adapters.solidworks.Drawing.Definition.Linked.Fields.ViewMiddle import (
    KViewMiddle,
)
from convert.adapters.solidworks.Drawing.Definition.Linked.Fields.ViewTail import (
    KViewTail,
)

# nested support planes require the view condition to end before the outer drawing resumes
KViewFields = MappingProxyType(
    {
        "moDrView.Archive": (*KViewLead, *KViewMiddle, *KViewTail),
        "moDrView": (
            NativeField(
                "Branch",
                "",
                ModeValue="Condition",
                MaskValue=64,
                BodyValue=(NativeField("Base", "moDrView.Archive"),),
                OtherValue=(
                    NativeField(
                        "Mask",
                        "conditions",
                        MaskValue=64,
                        BodyValue=(NativeField("Base", "moDrView.Archive"),),
                    ),
                ),
            ),
            NativeField(
                "Branch",
                "",
                ModeValue="Condition",
                MaskValue=1,
                BodyValue=(
                    NativeField("Scalar", "has_view_bodies", "i32"),
                    NativeField(
                        "Branch",
                        "has_view_bodies",
                        ModeValue="Nonzero",
                        BodyValue=(NativeField("Fail", "drawing view bodies"),),
                    ),
                ),
            ),
            NativeField("Embed", "f608", "mgBBox_c.restore"),
            *MakeScalarRows("f64", "f738 f740 f748 f750"),
            *MakeScalarRows("i32", "f55c ffbc f590 f594"),
            NativeField("Scalar", "f3f8", "f64"),
            NativeField("Text", "fff8"),
            *MakeScalarRows("i32", "f61c f7a0 f5a8"),
        ),
        "moAbsoluteView": (
            NativeField("Base", "moDrView"),
            NativeField("Scalar", "f1010", "u16"),
            NativeField("Text", "f1018"),
            NativeField("Scalar", "f1020", "u8"),
            *MakeScalarRows("i32", "f1028 f102c f1030"),
        ),
    }
)
