from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.Layouts.ReferenceFields import (
    KReferenceFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.ResolvedLayouts import (
    KResolvedLayouts,
)
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField

# occurrence and plane rows share the same measured state key and object list framing
KAttributeRows = (
    NativeField("Scalar", "key", "i32"),
    NativeField(
        "Array", "objs", "u32", BodyValue=(NativeField("Node", "o"),), CountValue="k"
    ),
)

# the fresh assembly visual store has a separate schema context from saved configuration bodies
KVisualFields = MappingProxyType(
    {
        **{
            NameValue: KResolvedLayouts[NameValue]
            for NameValue in (
                "moComponent_c",
                "moUnitComponent_c",
                "moCompRef_c",
                "moCompFeature_c",
                "moFRData_c",
                "moCStringHandle_c",
                "moReferencedConfiguration_c",
                "moSharedFileDef_c",
                "moExtObject_c",
            )
        },
        **{
            NameValue: KReferenceFields[NameValue]
            for NameValue in (
                "moChainComponent_c",
                "moContextChainComponent_c",
                "moReferenceChain_c",
                "moExtFeatureList_c",
                "moExtObjectInterface_c.FUN_4c179410",
            )
        },
        "moExtFeature_c": KReferenceFields["moExtFeature_c"][:-1],
        "visStateKeyData_c": (
            NativeField("Scalar", "f15c", "i32"),
            NativeField("Scalar", "f158", "i32"),
            NativeField(
                "Array",
                "f118",
                "i32",
                CountValue="n_ids",
                BodyValue=(
                    NativeField("Scalar", "key", "i32"),
                    NativeField("Scalar", "value", "i32"),
                    NativeField("Scalar", "one", "i32"),
                ),
            ),
            NativeField(
                "Array",
                "f0f0",
                "i32",
                CountValue="n_states",
                BodyValue=(
                    NativeField("Scalar", "id", "i32"),
                    NativeField("Text", "name"),
                    NativeField("Scalar", "f384", "i32"),
                    NativeField("Scalar", "f394", "i32"),
                    NativeField("Scalar", "f38c", "i32"),
                ),
            ),
            NativeField(
                "Array",
                "comps",
                "u32",
                CountValue="n_comps",
                BodyValue=(
                    NativeField("Node", "comp"),
                    NativeField(
                        "Array",
                        "attrs",
                        "u32",
                        CountValue="m",
                        BodyValue=KAttributeRows,
                    ),
                ),
            ),
            NativeField(
                "Array",
                "f78",
                "u32",
                CountValue="n_ents",
                BodyValue=(
                    NativeField("Node", "ref"),
                    NativeField(
                        "Array",
                        "attrs",
                        "u32",
                        CountValue="m",
                        BodyValue=KAttributeRows,
                    ),
                ),
            ),
            NativeField(
                "Array", "f88", "u32", CountValue="n_f88", BodyValue=KAttributeRows
            ),
            NativeField("Scalar", "n", "i32"),
        ),
        "visStateAttribute_c": (NativeField("Scalar", "f08", "u32"),),
        "visStateDisplayStateAttribute_c": (
            NativeField("Base", "visStateAttribute_c"),
            NativeField("Text", "f10"),
            NativeField("Scalar", "f18", "i32"),
        ),
        "visStateVisualPropertiesAttribute_c": (
            NativeField("Base", "visStateAttribute_c"),
            NativeField("Node", "f10"),
        ),
        "visStateVisualStateAttribute_c": (
            NativeField("Base", "visStateAttribute_c"),
            NativeField("Scalar", "f10", "i32"),
            NativeField("Scalar", "f14", "i32"),
            NativeField("Scalar", "f18", "i32"),
            NativeField("Scalar", "f1c", "i32"),
        ),
    }
)

# standalone visual graphs may allocate only the concrete measured parent visibility owners
KVisualSchemas = MappingProxyType(
    dict.fromkeys(
        (
            "moUnitComponent_c",
            "moCompFeature_c",
            "moCStringHandle_c",
            "moExtObject_c",
            "moContextChainComponent_c",
            "moReferenceChain_c",
            "moExtFeatureList_c",
            "moExtFeature_c",
            "visStateKeyData_c",
            "visStateDisplayStateAttribute_c",
            "visStateVisualPropertiesAttribute_c",
            "visStateVisualStateAttribute_c",
        ),
        (1,),
    )
)
