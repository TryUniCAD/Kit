from convert.adapters.solidworks.Drawing.Definition.Profiles.ReadProfileSet import (
    ReadProfileSet,
)
from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Drawing.Definition.Emission.CheckEmptyRows import (
    CheckEmptyRows,
)
from convert.adapters.solidworks.Drawing.Definition.Emission.Layouts.DetailFields import (
    KDetailFields,
)
from convert.adapters.solidworks.Drawing.Definition.Projection.ConceptFields import (
    NeedConceptMap,
)


# known incomplete branches must fail before an otherwise complete stream can escape the writer
def CheckBlankNode(NodeValue: ArchiveNode) -> None:
    ClassName = NodeValue.ClassValue.NameValue
    FieldsValue = NodeValue.FieldsValue
    if ClassName == "moLayerMgr_c" and (
        FieldsValue["layers"] or FieldsValue["f08"] is not None
    ):
        raise BodyUnsupported("blank drawing Definition excludes populated layers")
    if ClassName == "moLayerMask_c":
        MaskValue = NeedConceptMap(FieldsValue["f08"])
        if MaskValue["n"] != 0 or MaskValue.get("data", b"") != b"":
            raise BodyUnsupported(
                "blank drawing Definition excludes populated layer masks"
            )
    if ClassName == "moDetailFolder_c":
        if FieldsValue["has_fd98"] != 0:
            raise BodyUnsupported(
                "blank drawing Definition excludes annotation buckets"
            )
        _ = ReadProfileSet(NodeValue, 19000)
        for RuleValue in KDetailFields[ClassName]:
            if (
                RuleValue.TypeValue == "rf.suObList"
                and RuleValue.NameValue != "f8f8"
                and NeedConceptMap(FieldsValue[RuleValue.NameValue])["items"]
            ):
                raise BodyUnsupported(
                    "blank drawing Definition excludes sheet annotations"
                )
    if ClassName == "sgSketch":
        CheckEmptyRows(FieldsValue)
    if ClassName == "moSketchBlockMgr_c":
        BlockFields = NeedConceptMap(FieldsValue["blocks"])
        if BlockFields["f68"] or BlockFields["f90"]:
            raise BodyUnsupported(
                "blank drawing Definition excludes populated sketch blocks"
            )
