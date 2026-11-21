from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.PartMatFields import (
    KPartMatFields,
)
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Config.Material.MatTypes import KHatchClass
from convert.adapters.solidworks.Archive.Header.HeaderFields import KHeaderVersion

# both current texture branches use the same native restore layout
KMatTextureFields = (
    *(
        NativeField("Scalar", f"f{OffsetValue:02x}", "f64")
        for OffsetValue in range(8, 0x70, 8)
    ),
    NativeField("Text", "f70"),
    NativeField("Scalar", "f78", "i16"),
    NativeField("Scalar", "f7c", "i32"),
    NativeField("Scalar", "f80", "f64"),
    NativeField("Scalar", "f88", "f64"),
    NativeField("Scalar", "f9c", "i32"),
)


# named assignment inspection can read its visual owners without extending shared writer registries
def BindMatReadMut(ContextValue: BodyContext) -> None:
    if ContextValue.VersionValue != KHeaderVersion:
        raise BodyUnsupported(
            "SOLIDWORKS assigned material requires archive version 19000"
        )
    HatchName = KHatchClass.NameValue
    ContextValue.LayoutsValue = MappingProxyType(
        {
            **ContextValue.LayoutsValue,
            "uoMaterialTextureProperties.restore": KMatTextureFields,
            HatchName: KPartMatFields[HatchName],
        }
    )
    ContextValue.SchemasValue = MappingProxyType(
        {**ContextValue.SchemasValue, HatchName: (KHatchClass.SchemaValue,)}
    )
