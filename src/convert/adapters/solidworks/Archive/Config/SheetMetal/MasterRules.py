from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.ConceptFields import (
    KConceptFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.FeatureFields import (
    KFeatureFields,
)
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass

# the model bridge owns a concrete sheet metal master without a runtime class tag
KMasterClass = RuntimeClass("moSheetMetalMaster_c", 1)

# the ordinary master inherits the actual feature virtual bodies before its own rows
KMasterLayouts = MappingProxyType(
    {
        **KFeatureFields,
        **KConceptFields,
        KMasterClass.NameValue: (
            NativeField("Base", "moFeature_c"),
            NativeField("Length", "n370", "i32", CountValue="f358"),
            NativeField(
                "Branch",
                "n370",
                BodyValue=(
                    NativeField("Fail", "nonempty sheet metal master body list"),
                ),
                ModeValue="Nonzero",
            ),
        ),
    }
)

# virtual inheritance must resolve against the concrete direct feature rather than the part
KMasterVirtuals: MappingProxyType[tuple[str, int], str | int | bool | None] = (
    MappingProxyType(
        {
            (KMasterClass.NameValue, 1000): "moFeature_c.SerializeXmlData",
            (KMasterClass.NameValue, 1016): True,
            (KMasterClass.NameValue, 1208): "moConcept_c.SerializeLWData",
            (KMasterClass.NameValue, 1216): "moConcept_c.SerializeResolvedData",
        }
    )
)

# the signed selector belongs to the outer model and contributes no mapped node
KMasterBridge = (
    NativeField("Scalar", "f1014", "i32"),
    NativeField(
        "Branch",
        "f1014",
        BodyValue=(NativeField("DirectNode", "f1018", KMasterClass.NameValue),),
        ModeValue="Nonzero",
    ),
)
