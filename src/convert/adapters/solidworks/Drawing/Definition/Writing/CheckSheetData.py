from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.BodyWriter import BodyWriter
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Drawing.Identity.DrawingIdentity import (
    KDrawArchiveVersion,
)


# unsupported sheet owners and annotation branches must fail before any bytes are appended
def CheckSheetData(WriterValue: BodyWriter, NodeValue: ArchiveNode) -> None:
    ClassValue = NodeValue.ClassValue
    if (
        WriterValue.ContextValue.VersionValue != KDrawArchiveVersion
        or not isinstance(ClassValue, RuntimeClass)
        or (ClassValue.NameValue, ClassValue.SchemaValue) != ("moDrSheet", 1)
    ):
        raise BodyUnsupported(
            "sheet body requires version 19000 and moDrSheet schema one"
        )
    if WriterValue.ContextValue.FlagsValue.get("conditions", 0) != 0:
        raise BodyUnsupported(
            "sheet body requires its ordinary drawing archive context"
        )
    FieldsValue = NodeValue.FieldsValue
    if any(
        FieldName not in FieldsValue
        for FieldName in ("has_f408", "has_f468", "has_f418")
    ):
        raise BodyUnsupported("sheet body requires explicit native presence flags")
    if (
        FieldsValue["has_f450"] != 0
        or FieldsValue["f368_marker"] != 65535
        or FieldsValue["ink_views"]
    ):
        raise BodyUnsupported(
            "sheet body has unqualified annotation or ink view fields"
        )
