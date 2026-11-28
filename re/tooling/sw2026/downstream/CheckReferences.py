from codecs import lookup
from hashlib import sha256
from json import dumps
from struct import pack
from sys import addaudithook

from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from downstream.Body import COLLECTIONS, PREFIX, ROOT
from downstream.Components import read_component_body, write_component_body


VERTEX_WORDS = (302, 119, -381, 753)
EDGE_WORDS = (42, -88, 173, 1524)
MATCH_ROWS = (
    {"f08": -12, "f0c": 0x8a00000c, "f10": 382, "f14": -1},
    {"f08": 18, "f0c": 266, "f10": 0x90001753, "f14": 11},
)
EMBEDDED_ROWS = {
    "f10": [{"key": 8, "value": -32}, {"key": -4, "value": 69}, {"key": 8, "value": 93}],
    "f20": [{"value": -63}, {"value": 0}, {"value": 91}],
    "f38": -82,
    "f40_0": 8053,
    "f40_1": -771,
}


def node(name, fields):
    return ArchiveNode(RuntimeClass(name, 1), fields)


def entity_reference_fields(representations, vertex=None):
    return {
        "f60": 17, "f64": 209, "f08": len(representations), "fe8": 6, "f70": 472,
        "f28": 0.03125, "f30": 0.0625, "f40": vertex,
        "f10": [{"f08": value} for value in representations],
        "f48": 85, "fd0": [{"t0": 0xffffffff, "t1": 25}], "fec": 19000, "has_f18": 0,
    }


def make_body(drawing):
    fields = {name: index for index, name in enumerate(PREFIX, 1)}
    fields |= {field.NameValue: [] for field in COLLECTIONS}
    fields |= {"f30": "24cb57fc-11b0-4a31-9235-424ce7a2234e", "f38_high": 8, "f38_low": 6}

    end = node("moEndFaceSurfIdRep_c", {"f10": {"f08": None, "f10": None}, "f38": 22, "f3c": -9})
    sketch = node("moFromSktEntSurfIdRep_c", {"f10": {"f08": end, "f10": None}, "f38": 47})
    fields["f40"] = [{"object": end}, {"object": sketch}]

    vertex_fields = entity_reference_fields((end,))
    vertex_fields |= {"has_point": 1, "point": {"x": 0.25, "y": -0.03125, "z": 0.125}}
    if drawing:
        vertex_fields |= dict(zip(("ff8", "ffc", "f100", "f104"), VERTEX_WORDS, strict=True))
    vertex = node("moVertexRef_c", vertex_fields)
    face = node("moFaceRef_c", entity_reference_fields((sketch, end), vertex) | {
        "has_f18": 1, "f18": EMBEDDED_ROWS, "ff0": MATCH_ROWS,
    })
    edge = node("moEdgeRef_c", entity_reference_fields((end,), vertex))

    base = dict.fromkeys(("f68", "f18", "f1c", "f20", "f30", "f70", "f84", "fa0", "f34", "f48"), 0)
    base |= dict.fromkeys(("has_fb0", "has_fb8", "has_fc0", "has_fc8", "has_fd0"), 0)
    base |= {"f58": None, "f4c": 19000, "f90": -1, "f94": -1, "f98": -1, "f9c": -1}
    component = {**base, "alias_present": 0, "ff0": None}
    comp_face = node("moCompFace_c", {**component, "alias_present": 1, "f08": "support", "fe8": face})
    comp_vertex = node("moCompVertex_c", {**component, "fe8": vertex})
    edge_fields = {
        **component, "fe8": edge, "f188": 8, "f18c": 19, "f130": [{"object": comp_vertex}],
        "f158": {"x": 0.015625, "y": 0.03125, "z": 0.046875},
        "f170": {"x": 0.0625, "y": 0.078125, "z": 0.09375},
    }
    composite = node("moCompCompositeEdge_c", {**edge_fields, "f188": 14, "f130": []})
    edge_fields |= {"f190": composite, "f198": None}
    if drawing:
        edge_fields |= dict(zip(("f1b4", "f1b8", "f1bc", "f1c0"), EDGE_WORDS, strict=True))
    comp_edge = node("moCompEdge_c", edge_fields)
    atom_fields = {**base, "ff0": face, "n110": 2, "f110": [{"v": 201}, {"v": -709}],
                   "f108": 47, "f104": 258, "f100": 871}
    solid = node("moCompSolidBody_c", dict(atom_fields))
    surface = node("moCompSurfaceBody_c", dict(atom_fields))
    sections = {"f48": comp_face, "f60": comp_edge, "f78": comp_vertex, "f90": solid, "fa8": surface}
    for i, (section, value) in enumerate(sections.items(), 1):
        fields[section] = [{"object": value, "word": 1000 + i}]
    fields["f180"] = [{"key": 2, "object": comp_edge, "word": -8}]
    return ArchiveNode(ROOT, fields)


def check_aliases(loaded, drawing, raw):
    fields = loaded.FieldsValue
    comp_face = fields["f48"][0]["object"]
    comp_edge = fields["f60"][0]["object"]
    comp_vertex = fields["f78"][0]["object"]
    edge = comp_edge.FieldsValue
    composite = edge["f190"].FieldsValue
    face = comp_face.FieldsValue["fe8"]
    vertex = comp_vertex.FieldsValue["fe8"]
    end, sketch = (row["object"] for row in fields["f40"])
    assert fields["f180"][0]["object"] is comp_edge
    assert edge["f130"][0]["object"] is comp_vertex
    assert edge["fe8"] is composite["fe8"]
    assert "f190" not in composite and edge["f198"] is None
    assert fields["f90"][0]["object"].FieldsValue["ff0"] is face
    assert fields["fa8"][0]["object"].FieldsValue["ff0"] is face
    assert face.FieldsValue["f40"] is vertex
    assert edge["fe8"].FieldsValue["f40"] is vertex
    assert sketch.FieldsValue["f10"]["f08"] is end
    assert vertex.FieldsValue["f10"][0]["f08"] is end
    assert face.FieldsValue["f10"][0]["f08"] is sketch
    assert face.FieldsValue["f10"][1]["f08"] is end
    assert edge["fe8"].FieldsValue["f10"][0]["f08"] is end
    assert face.FieldsValue["ff0"] == list(MATCH_ROWS)
    embedded = face.FieldsValue["f18"]
    assert {name: embedded[name] for name in EMBEDDED_ROWS} == EMBEDDED_ROWS
    assert (embedded["n10"], embedded["n20"]) == (3, 3)
    match = b"".join(pack("<iIIi", *(row[key] for key in ("f08", "f0c", "f10", "f14"))) for row in MATCH_ROWS)
    embedded_expected = pack("<13i", 3, 8, -32, -4, 69, 8, 93, 3, -63, 0, 91, -82, 8053) + pack("<i", -771)
    assert raw.count(pack("<i", 2) + match) == 1
    assert raw.count(embedded_expected) == 1
    assert raw.count(pack("<i3d", 1, 0.25, -0.03125, 0.125)) == 1
    assert raw.count(pack("<4i", *VERTEX_WORDS)) == int(drawing)
    assert raw.count(pack("<4i", *EDGE_WORDS)) == int(drawing)


def roundtrip(drawing):
    raw, initial = write_component_body(make_body(drawing), drawing=drawing)
    loaded, snapshot = read_component_body(raw, drawing=drawing)
    reemitted, final = write_component_body(loaded, drawing=drawing)
    assert raw == reemitted and snapshot == final
    assert initial.CounterValue == snapshot.CounterValue == 23
    classes = sorted(slot.EntryValue.NameValue for slot in snapshot.EntriesValue
                     if type(slot.EntryValue) is RuntimeClass)
    assert len(classes) == 11
    assert tuple(slot.IndexValue for slot in snapshot.EntriesValue) == tuple(range(1, 23))
    assert snapshot.EntriesValue[0].EntryValue.NameValue == "moEndFaceSurfIdRep_c"
    assert snapshot.EntriesValue[1].EntryValue is loaded.FieldsValue["f40"][0]["object"]
    check_aliases(loaded, drawing, raw)
    return raw, {"bytes": len(raw), "sha256": sha256(raw).hexdigest(), "classes": classes,
                 "counter": snapshot.CounterValue, "map_slots": len(snapshot.EntriesValue)}


def invalid_body(case):
    drawing = case == "drawing_tail_in_part"
    root = make_body(drawing)
    edge = root.FieldsValue["f60"][0]["object"].FieldsValue
    face = root.FieldsValue["f48"][0]["object"].FieldsValue
    atom = root.FieldsValue["f90"][0]["object"].FieldsValue
    if case == "bad_entity_count":
        face["fe8"].FieldsValue["f08"] = 5
    elif case == "bad_atom_count":
        atom["n110"] = 7
    elif case == "foreign_component_reference":
        face["fe8"] = edge["fe8"]
    elif case == "foreign_vertex_reference":
        face["fe8"].FieldsValue["f40"] = edge["fe8"]
    elif case == "foreign_edge_link":
        edge["f190"] = root.FieldsValue["f48"][0]["object"]
    return root


def main():
    for encoding in ("latin-1", "cp1252", "utf-16le", "utf-8"):
        lookup(encoding)
    events = []
    active = True

    def guard(event, args):
        if active and event in ("open", "subprocess.Popen", "socket.connect"):
            events.append(event)
            raise RuntimeError("external operation during downstream component replay")

    addaudithook(guard)
    try:
        part, part_info = roundtrip(False)
        drawing, drawing_info = roundtrip(True)
        assert len(drawing) - len(part) == 32
        controls = {}
        for case in (
            "bad_entity_count", "bad_atom_count", "foreign_component_reference",
            "foreign_vertex_reference", "foreign_edge_link", "drawing_tail_in_part",
        ):
            try:
                write_component_body(invalid_body(case))
            except ValueError as error:
                controls[case] = str(error)
            else:
                raise AssertionError(f"accepted {case}")
        for case, wire, mode in (
            ("part_in_drawing_context", part, True), ("drawing_in_part_context", drawing, False),
            ("truncated_drawing", drawing[:-1], True),
        ):
            try:
                read_component_body(wire, drawing=mode)
            except ValueError as error:
                controls[case] = type(error).__name__
            else:
                raise AssertionError(f"accepted {case}")
    finally:
        active = False
    print(dumps({
        "passed": True, "ordinary_part": part_info, "drawing_context": drawing_info,
        "drawing_tail_bytes": len(drawing) - len(part), "refusals": controls,
        "independent_match_rows": len(MATCH_ROWS), "independent_embedded_rows": 6,
        "runtime_io_attempts": len(events), "native_runs": 0, "native_cache_samples_read": 0,
    }, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
