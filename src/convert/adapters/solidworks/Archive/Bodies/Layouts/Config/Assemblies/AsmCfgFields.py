from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.Assemblies.AsmFileFields import (
    KExternalFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.Assemblies.AssemblyFields import (
    KAssemblyFields,
)
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# assembly configuration extends the shared model with its actual reference owners and directory maps
KAsmCfgFields = MappingProxyType(
    {
        **KAssemblyFields,
        **KExternalFields,
        "moComponent_c": (NativeField("Node", "owner"),),
        "moExtFeature_c": (
            NativeField("Base", "moExtObjectInterface_c.FUN_4c179410"),
            NativeField("Node", "f50"),
            NativeField("Scalar", "f58", "i32"),
        ),
        "moExtObjectInterface_c.FUN_4c179410": (
            NativeField("Embed", "f10", "moSharedFileDef_c"),
            NativeField("Embed", "f18", "moReferencedConfiguration_c"),
            NativeField("Scalar", "f40", "u8"),
            NativeField("Scalar", "f44", "i32"),
            NativeField("Node", "f38"),
        ),
        "su_CMapStringToString": (
            NativeField(
                "Array",
                "items",
                "Framework",
                BodyValue=(NativeField("Text", "k"), NativeField("Text", "v")),
                CountValue="n",
            ),
        ),
    }
)
