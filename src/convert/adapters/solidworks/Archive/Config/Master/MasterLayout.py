from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.ConceptFields import (
    KConceptFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.FeatureFields import (
    KFeatureFields,
)
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass

# the part owns this concrete body through a direct field selected by its flag
KMasterClass = RuntimeClass("moSheetMetalMaster_c", 1)

# the enclosing part identifies the untagged body through this resolved field
KMasterField = "f1018"

# the caller consumes the part flag before entering the untagged master body
KMasterRule = (NativeField("DirectNode", KMasterField, KMasterClass.NameValue),)

# native inherited feature data precedes the master body list count
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
                ModeValue="NotEquals",
            ),
        ),
    }
)

# the master dispatches inherited fields through its own native virtual slots
KMasterVirtuals: MappingProxyType[tuple[str, int], str | bool] = MappingProxyType(
    {
        (KMasterClass.NameValue, 1000): "moFeature_c.SerializeXmlData",
        (KMasterClass.NameValue, 1016): True,
        (KMasterClass.NameValue, 1208): "moConcept_c.SerializeLWData",
        (KMasterClass.NameValue, 1216): "moConcept_c.SerializeResolvedData",
    }
)
