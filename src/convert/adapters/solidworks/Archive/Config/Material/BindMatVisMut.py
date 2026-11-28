from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.Visual.MatTextureFields import (
    KMatTextureFields,
)
from convert.adapters.solidworks.Archive.Header.HeaderFields import KHeaderVersion


# assigned material inspection uses the exact current texture member in its fresh read context
def BindMatVisMut(ContextValue: BodyContext) -> None:
    if (
        ContextValue.VersionValue != KHeaderVersion
        or ContextValue.UsageValue.SchemaCalls
    ):
        raise BodyUnsupported(
            "unqualified SOLIDWORKS assigned material archive context"
        )
    ContextValue.LayoutsValue = {
        **ContextValue.LayoutsValue,
        "uoMaterialTextureProperties.restore": KMatTextureFields,
    }
