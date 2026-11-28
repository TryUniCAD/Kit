from convert.adapters.solidworks.Archive.Bodies.Layouts.ExternalFields import KExternalFields
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.ComponentFields import KComponentFields
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.FeatureFields import KFeatureFields
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.GeometryFields import KGeometryFields
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.ReferenceFields import KReferenceFields
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from downstream.Body import scalar


DRAWING_MODEL = "drawing_model"
REFERENCE_CLASSES = ("moFaceRef_c", "moEdgeRef_c", "moVertexRef_c")
ENTITY_REPRESENTATIONS = ("moEndFaceSurfIdRep_c", "moFromSktEntSurfIdRep_c")
FEATURE_REFERENCE_CLASSES = ("moFR_c", "moExtObject_c", "moCStringHandle_c")
VERTEX_DRAWING_FIELDS = ("ff8", "ffc", "f100", "f104")


def drawing_words(names):
    return NativeField(
        "Branch",
        "",
        BodyValue=tuple(scalar(name, "i32") for name in names),
        ModeValue="Expression",
        ExpressionValue=("bool", ("lookup_or", ("context",), ("literal", DRAWING_MODEL), ("literal", 0))),
    )


def counted_body(name, count, *fields):
    return NativeField("Array", name, "i32", fields, CountValue=count)


_REFERENCE_DEPENDENCIES = (
    "moBEntRef_c", "moFaceRef_c", "moEntityId_c", "moEntityIdRep_c.FUN_4bba8de0",
    "er.FUN_4bba8790", "er.FUN_4bba41f0.FUN_4bbabca0", "er.FUN_4bbaa6a0", "er.FUN_4bbabca0",
    *ENTITY_REPRESENTATIONS,
)
REFERENCE_LAYOUTS = {
    **{name: KReferenceFields[name] for name in _REFERENCE_DEPENDENCIES},
    **KExternalFields,
    "moFR_c": KFeatureFields["moFR_c"],
    "moFRData_c": KComponentFields["moFRData_c"],
    "mgPoint_c.operator>>": KGeometryFields["mgPoint_c.operator>>"],
    "moEdgeRef_c": (NativeField("Base", "moBEntRef_c"),),
    "moVertexRef_c": (
        NativeField("Base", "moBEntRef_c"),
        scalar("has_point", "i32"),
        NativeField(
            "Branch", "has_point", BodyValue=(NativeField("Embed", "point", "mgPoint_c.operator>>"),),
            ModeValue="Nonzero",
        ),
        drawing_words(VERTEX_DRAWING_FIELDS),
    ),
    "moMultiMatchFaceData_c.FUN_4b75af80": (
        scalar("f08", "i32"), scalar("f0c", "u32"), scalar("f10", "u32"), scalar("f14", "i32"),
    ),
    "moEntRefDownstreamIdData_c": (
        counted_body("f10", "n10", scalar("key", "i32"), scalar("value", "i32")),
        counted_body("f20", "n20", scalar("value", "i32")),
        scalar("f38", "i32"), scalar("f40_0", "i32"), scalar("f40_1", "i32"),
    ),
}
