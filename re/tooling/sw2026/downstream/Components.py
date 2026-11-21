from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.ModelFields import KModelFields
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.ComponentFields import KComponentFields
from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from downstream.Body import (
    DOWNSTREAM_CONTEXT, LAYOUTS, collection, read_standalone_body, scalar, write_standalone_body,
)
from downstream.References import (
    DRAWING_MODEL, ENTITY_REPRESENTATIONS, FEATURE_REFERENCE_CLASSES, REFERENCE_CLASSES, REFERENCE_LAYOUTS,
    VERTEX_DRAWING_FIELDS, drawing_words,
)


COMMON = (
    NativeField("Base", "moCompRef_c"),
    scalar("alias_present", "u8"),
    NativeField("Branch", "alias_present", ModeValue="Nonzero", BodyValue=(NativeField("Text", "f08"),)),
    NativeField("Node", "fe8", "moBEntRef_c"),
    NativeField("Node", "ff0", "moExtObject_c"),
)
FLAGS = ("lookup", ("scope",), ("literal", "f188"))
EXTRA_LINKS = (
    "And",
    ("compare", ("NotEq",), ("BitAnd", FLAGS, ("literal", 6)), ("literal", 6)),
    ("compare", ("NotEq",), ("BitAnd", FLAGS, ("literal", 8)), ("literal", 0)),
)
COMPOSITE = (
    NativeField("Base", "moCompBEntRef_c"),
    scalar("f188", "i32"),
    NativeField("Embed", "f158", "mgPoint_c.operator>>"),
    NativeField("Embed", "f170", "mgPoint_c.operator>>"),
    scalar("f18c", "u32"),
    collection("f130", NativeField("Node", "object")),
    NativeField(
        "Branch", "f188", ModeValue="Expression", ExpressionValue=EXTRA_LINKS,
        BodyValue=(NativeField("Node", "f190", "moCompCompositeEdge_c"),
                   NativeField("Node", "f198", "moCompCompositeEdge_c")),
    ),
)
EDGE_DRAWING_FIELDS = ("f1b4", "f1b8", "f1bc", "f1c0")
ATOM_CLASSES = ("moCompSolidBody_c", "moCompSurfaceBody_c")
EDGE_CLASSES = ("moCompCompositeEdge_c", "moCompEdge_c")
UNIT_COMPONENT_CLASS = "moUnitComponent_c"
COMPONENT_REFERENCES = {
    "moCompFace_c": "moFaceRef_c",
    "moCompVertex_c": "moVertexRef_c",
    "moCompEdge_c": "moEdgeRef_c",
    "moCompCompositeEdge_c": "moEdgeRef_c",
}
CONCRETE_COMPONENTS = {
    "moCompFace_c": COMMON,
    "moCompVertex_c": COMMON,
    "moCompCompositeEdge_c": COMPOSITE,
    "moCompEdge_c": (NativeField("Base", "moCompCompositeEdge_c"), drawing_words(EDGE_DRAWING_FIELDS)),
    **{name: KComponentFields["moCompSolidBody_c"] for name in ATOM_CLASSES},
}
COMPONENT_LAYOUTS = {
    **LAYOUTS,
    **REFERENCE_LAYOUTS,
    "moCompRef_c": KComponentFields["moCompRef_c"],
    "moCompBEntRef_c": COMMON,
    "moComponent_c": (NativeField("Node", "owner"),),
    UNIT_COMPONENT_CLASS: KModelFields[UNIT_COMPONENT_CLASS],
    **CONCRETE_COMPONENTS,
}
SCHEMAS = {
    name: (1,) for name in (
        *LAYOUTS, *CONCRETE_COMPONENTS, *REFERENCE_CLASSES, *ENTITY_REPRESENTATIONS,
        *FEATURE_REFERENCE_CLASSES, UNIT_COMPONENT_CLASS,
    )
}


def component_context(drawing):
    if type(drawing) is not bool:
        raise TypeError("downstream drawing context must be boolean")
    return BodyContext(19000, COMPONENT_LAYOUTS, {}, SCHEMAS,
                       FlagsValue={DOWNSTREAM_CONTEXT: 1, DRAWING_MODEL: int(drawing)})


def assert_pointer(value, expected, field):
    if value is not None and (type(value) is not ArchiveNode or value.ClassValue.NameValue not in expected):
        raise ValueError(f"{field} requires its declared downstream pointer kind")


def assert_fields(fields, names, present):
    owned = sum(name in fields for name in names)
    if owned != (len(names) if present else 0):
        raise ValueError(f"{names[0]} presence disagrees with the downstream serialization branch")


def validate_reference(name, fields, drawing):
    assert_pointer(fields["f40"], ("moVertexRef_c",), "entity reference f40")
    if fields["f08"] != len(fields["f10"]):
        raise ValueError("entity reference count disagrees with the inline ID bodies")
    for row in fields["f10"]:
        assert_pointer(row["f08"], ENTITY_REPRESENTATIONS, "inline entity ID")
    assert_fields(fields, ("f18",), bool(fields["has_f18"]))
    if name == "moVertexRef_c":
        assert_fields(fields, ("point",), bool(fields["has_point"]))
        assert_fields(fields, VERTEX_DRAWING_FIELDS, drawing)


def validate_component(name, fields, drawing):
    assert_pointer(fields["f58"], (UNIT_COMPONENT_CLASS,), "owning component f58")
    if name in ATOM_CLASSES:
        assert_pointer(fields["ff0"], ("moFaceRef_c",), "atom ff0")
        if fields["n110"] != len(fields["f110"]):
            raise ValueError("atom count disagrees with its identifier array")
        return
    assert_pointer(fields["fe8"], (COMPONENT_REFERENCES[name],), "component fe8")
    assert_pointer(fields["ff0"], (), "component extension ff0")
    assert_fields(fields, ("f08",), bool(fields["alias_present"]))
    if name in EDGE_CLASSES:
        links = fields["f188"] & 6 != 6 and fields["f188"] & 8 != 0
        assert_fields(fields, ("f190", "f198"), links)
        if links:
            assert_pointer(fields["f190"], EDGE_CLASSES, "edge f190")
            assert_pointer(fields["f198"], EDGE_CLASSES, "edge f198")
    if name == "moCompEdge_c":
        assert_fields(fields, EDGE_DRAWING_FIELDS, drawing)


def validate_graph(snapshot, drawing):
    for slot in snapshot.EntriesValue:
        value = slot.EntryValue
        if type(value) is not ArchiveNode:
            continue
        name = value.ClassValue.NameValue
        if name in CONCRETE_COMPONENTS:
            validate_component(name, value.FieldsValue, drawing)
        elif name in REFERENCE_CLASSES:
            validate_reference(name, value.FieldsValue, drawing)
        elif name in ENTITY_REPRESENTATIONS:
            fields = value.FieldsValue["f10"]
            assert_pointer(fields["f08"], ENTITY_REPRESENTATIONS, "nested entity ID")
            assert_pointer(fields["f10"], ("moFR_c",), "feature reference")
        elif name == "moFR_c":
            assert_pointer(value.FieldsValue["f08"], ("moExtObject_c",), "feature reference file")
        elif name == UNIT_COMPONENT_CLASS:
            fields = value.FieldsValue
            if fields.keys() != {"owner", "has_ext"} or fields["owner"] is not None or fields["has_ext"] != 0:
                raise ValueError("standalone local unit component requires its implicit filed owner")


def make_local_unit_component(part):
    model = part.SystemValue.RootValue
    config = part.CurrentConfig
    if model.ClassValue.NameValue != "moPart_c" or config.ClassValue.NameValue != "moPartConfiguration_c":
        raise ValueError("local unit component requires its actual ordinary part configuration")
    if config.FieldsValue.get("owner") is not model:
        raise ValueError("local unit component belongs to a different part model")
    return ArchiveNode(RuntimeClass(UNIT_COMPONENT_CLASS, 1), {"owner": None, "has_ext": 0})


def read_component_body(raw, *, drawing=False):
    body, snapshot = read_standalone_body(
        raw, component_context(drawing), entity_representations=ENTITY_REPRESENTATIONS,
    )
    validate_graph(snapshot, drawing)
    return body, snapshot


def write_component_body(body, *, drawing=False):
    raw, snapshot = write_standalone_body(
        body, component_context(drawing), entity_representations=ENTITY_REPRESENTATIONS,
    )
    validate_graph(snapshot, drawing)
    return raw, snapshot
