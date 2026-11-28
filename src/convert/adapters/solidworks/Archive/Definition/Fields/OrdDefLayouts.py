from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.FontFields import (
    KFontFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.GeometryFields import (
    KGeometryFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.PartMatFields import (
    KPartMatFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.ContainerFields import (
    KContainerFields,
)
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Definition.Fields.DocEnvironmentFields import (
    KDocEnvironmentFields,
    SplitterFields,
)
from convert.adapters.solidworks.Archive.Definition.Fields.DocHeadFields import (
    KDefRenderer,
    KDocHeadPrefix,
)
from convert.adapters.solidworks.Archive.Definition.Fields.DocHelperFields import (
    KDocHelperFields,
)
from convert.adapters.solidworks.Archive.Definition.Fields.DocStyleFields import (
    KDocStyleFields,
)
from convert.adapters.solidworks.Archive.Definition.Fields.DocTailFields import (
    KPartDefTail,
)
from convert.adapters.solidworks.Archive.Definition.Fields.DocTransformFields import (
    KDocTransformFields,
)
from convert.adapters.solidworks.Archive.Definition.Fields.ScalarFields import (
    MakeScalarRows,
)

# ordinary parts reject alternate renderer markers before reading an embedded owner
KOrdDefRenderer = NativeField(
    "Branch",
    "has_pwmaterial",
    BodyValue=(
        NativeField(
            "Branch",
            "has_pwmaterial",
            BodyValue=(NativeField("Fail", "alternate renderer marker"),),
            OtherValue=(KDefRenderer,),
            ModeValue="NotEquals",
            MaskValue=1,
        ),
    ),
    ModeValue="Nonzero",
)

# the narrow profile keeps the ordinary manager list and the proved shared helpers
KOrdDefLayouts = MappingProxyType(
    {
        **{
            NameValue: KContainerFields[NameValue]
            for NameValue in (
                "su_CObArray",
                "su_CDWordArray",
                "su_CStringArray",
                "suObList",
            )
        },
        **KGeometryFields,
        **KFontFields,
        **KDocEnvironmentFields,
        **{
            NameValue: FieldRows
            for NameValue, FieldRows in KDocHelperFields.items()
            if NameValue != "uoSketch"
        },
        **KDocStyleFields,
        **KDocTransformFields,
        "uiSplitterInfo_c.Serialize": SplitterFields(False),
        "uoModelData_c.restore": KPartMatFields["uoModelData_c"],
        "PWMaterialManager_c.restore": (
            *MakeScalarRows("i32", "f08 f0c"),
            NativeField("Embed", "list", "suObList"),
        ),
        "uiPartDoc_c": (*KDocHeadPrefix, KOrdDefRenderer, *KPartDefTail),
    }
)
