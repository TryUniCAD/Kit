from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Definition.Fields.DocEnvironmentFields import (
    KDocEnvironmentFields,
)
from convert.adapters.solidworks.Drawing.Definition.Linked.Fields.CompFields import (
    KCompGate,
)

# drawing contexts omit the primary splitter while retaining the exact shared secondary grid and all presentation words
KDrawingEnvironmentFields = MappingProxyType(
    {
        "uiUserModelEnv_c": (
            NativeField(
                "Branch",
                "",
                BodyValue=tuple(
                    FieldValue
                    for FieldValue in KDocEnvironmentFields["uiUserModelEnv_c"]
                    if FieldValue.NameValue != "f10"
                ),
                OtherValue=(
                    NativeField(
                        "Fail", "user model environment outside drawing context"
                    ),
                ),
                ModeValue="Expression",
                ExpressionValue=KCompGate,
            ),
        ),
    }
)
