from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField


# imported solids need their own typed local storage boundary after the inherited feature fields
KImportFields = MappingProxyType(
    {
        "moBaseBody_c": (
            NativeField("Validate", "OrdinaryLocalBaseBody"),
            NativeField("Base", "moBodyFeature_c"),
            NativeField("Text", "source_filename"),
            NativeField("Scalar", "local_body_switch", "i32"),
            NativeField(
                "Branch",
                "local_body_switch",
                OtherValue=(NativeField("Fail", "unsupported base body storage mode"),),
                ModeValue="Equals",
                MaskValue=1,
            ),
            NativeField("Text", "local_storage_key"),
            NativeField(
                "Array",
                "segment_mesh_ids",
                "i32",
                BodyValue=(NativeField("Scalar", "feature_id", "i32"),),
                CountValue="segment_mesh_count",
            ),
        ),
    }
)
