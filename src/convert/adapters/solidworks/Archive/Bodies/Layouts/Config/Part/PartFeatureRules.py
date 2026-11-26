from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# the direct sheet metal master has its own type and empty body list in this profile
KPartFeatureRules = MappingProxyType(
    {
        "moSheetMetalMaster_c": (
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
