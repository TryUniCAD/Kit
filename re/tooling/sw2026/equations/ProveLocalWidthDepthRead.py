import argparse
from hashlib import sha256
from importlib import import_module
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[4]
MANAGED = Path("/Users/odin/Documents/UniCAD/Oracle121Takeover")
D02 = Path("EquationSourceProtocol01/NativePacket01/Disclosed/D02/Native")
MATCHED = Path("WidthDepthSameLocator02")
ARCHIVE = "Contents/Config-0"
RESOLVED = "solidworks.typed_resolved_semantics"
CONFIG = "solidworks.typed_configuration_graph"
ACTUAL = (
    ("authored_original", D02 / "Original.SLDPRT", "8d79922604aba1816348ae2b62d3601c44a088dccf4b1373dd17ca0e39b02e58",
     (26, 34), (43.7, 18.1, 21.85), "AnchorSketch", "AnchorBoss", "Default", (193, 320), 3),
    ("authored_edit", D02 / "Edited.SLDPRT", "6f576c8aa8badc4209b14c081250bb917086433dccbcc2b25bba6c4b44339880",
     (26, 34), (58.3, 18.1, 29.15), "AnchorSketch", "AnchorBoss", "Default", (193, 320), 3),
    ("generated_reference", MATCHED / "Frozen/Reference.SLDPRT", "214935d57e37c22eee826ccdb20625a3038560b171e4d0e2abf63a83fd1cc9b8",
     (18, 21), (39.125, 17.375, 19.5625), "Sketch1", "Boss-Extrude1", "modeled default", (163, 256), None),
    ("native_saved_reference", MATCHED / "Inspection/ReferenceEdit/Edited.SLDPRT", "0c381bd6bb08b18e821a938731faca4608218959d9955c2516313550566a48af",
     (18, 21), (47.875, 17.375, 23.9375), "Sketch1", "Boss-Extrude1", "modeled default", (198, 338), 3),
)
PLAIN = (
    ("generated_plain", MATCHED / "Frozen/Plain.SLDPRT", "3b07ce7717313562b6ac3cc91b0d479d59f4e735d64d393d5848e438592317b9",
     (39.125, 17.375, 19.5625), 0),
    ("native_saved_plain", MATCHED / "Inspection/PlainEdit/Edited.SLDPRT", "c56057700a597bf885d8b43fad2660372c3566125a41fa7d307f3000637efc5e",
     (47.875, 17.375, 19.5625), 3),
)
GLOBAL = ROOT / "re/solidworks/examples/Single Turbo Dual Overhead Cam V8 - KDP - 2024/BLOQUE V8.SLDPRT"
GLOBAL_SHA = "a4611e1bebd809d421c49e772de65e75513c013d57e4bc4379e36f65f49b5851"
CORE = ROOT / "src/convert/adapters/solidworks/Core"


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def open_read(path, expected_sha, **options):
    from convert import open_document

    require(digest(path) == expected_sha, f"disclosed source hash differs for {path.name}")
    result = open_document(path, **options)
    require(result.source.sha256 == expected_sha, f"SDK read of {path.name} did not bind the disclosed bytes")
    return result


def parameters(doc, features, values, role, refs, right_text):
    sketch, boss = features
    keys = (f"sldprt:parameter:{sketch}:D1", f"sldprt:parameter:{sketch}:D2", f"sldprt:parameter:{boss}:D1")
    require(tuple(row.id for row in doc.parameters) == keys, "public live D1/D2/D1 IDs differ")
    width, height, depth = doc.parameters
    require(tuple(row.owner_id for row in (width, height, depth))
            == (f"sldprt:feature:{sketch}", f"sldprt:feature:{sketch}", f"sldprt:feature:{boss}"),
            "public parameter owners differ")
    require(tuple(row.value.value for row in (width, height, depth)) == values, "live length values differ")
    require(all(row.value.unit == "mm" and row.value.kind.value == "length" for row in (width, height, depth)),
            "public live units differ")
    require(all(row.role.value == "driving" and row.expression is None for row in (width, height)), "sketch drivers differ")
    require(depth.role.value == role, "depth role differs")
    if right_text is None:
        require(depth.expression is None, "plain control acquired an equation")
    else:
        equation = depth.expression
        require(equation is not None and (equation.source, equation.parameter_ids, equation.language)
                == (right_text, refs, "solidworks"), "public relation text or dependency differs")
    return width, height, depth


def read_actual(managed, row):
    name, relative, expected_sha, features, values, sketch, boss, config, maps, payloads = row
    location = managed / relative
    options = {"configuration": config}
    if payloads is None:
        from convert.adapters.solidworks.Container.Container import SldprtFormatError

        try:
            open_read(location, expected_sha, **options)
        except SldprtFormatError as error:
            require(str(error) == "SLDPRT contains no readable Parasolid payload", "cold geometry refusal changed")
            geometry_refusal = str(error)
        else:
            raise ValueError("uncached relation bypassed the existing geometry policy")
        options["include_brep"] = False
    else:
        geometry_refusal = None
    doc = open_read(location, expected_sha, **options)
    width, _, depth = parameters(
        doc, features, values, "derived", (f"sldprt:parameter:{features[0]}:D1",), f'"D1@{sketch}" / 2')
    require(depth.attributes["equation_source"] == f'"D1@{boss}" = "D1@{sketch}" / 2'
            and depth.attributes["equation_configuration_id"] == 0, "authored equation provenance differs")
    graph = doc.metadata[RESOLVED]
    proof = graph["local_width_depth_equation"]
    config_graph = doc.metadata[CONFIG]
    require(graph["status"] == "supplemented" and config_graph["status"] == "complete"
            and (config_graph["map_counter"], graph["map_counter"]) == maps
            and not graph["public_writer_qualified"], "typed graph boundary or counter differs")
    require(not any(diag.code == "solidworks.typed_configuration_graph_unavailable"
                    or "typed resolved semantics unavailable" in diag.message for diag in doc.diagnostics),
            "qualified relation retained a false diagnostic")
    require(depth.provenance is not None and len(depth.provenance.spans) == 2,
            "qualified depth needs both scalar and actual relation provenance")
    (scalar_span, relation_span) = depth.provenance.spans
    scalar = depth.attributes["typed_archive_owner"]
    relation = proof["relation"]
    require(all(span.record_kind == "typed-archive-object" and (span.stream, span.offset, span.length)
                == (owner["stream"], owner["offset"], owner["end"] - owner["offset"])
                for span, owner in ((scalar_span, scalar), (relation_span, relation))),
            "public spans differ from typed scalar or relation ownership")
    typed_width = width.attributes["typed_archive_owner"]
    require(proof["dependency"]["live_handle"]["object_index"] == typed_width["handle_index"]
            and proof["target"]["live_handle"]["object_index"] == scalar["handle_index"]
            and proof["dependency"]["component"]["object_index"] != proof["target"]["component"]["object_index"]
            and all(ref["live_handle"]["object_index"] != ref["cloned_handle"]["object_index"]
                    for ref in (proof["dependency"], proof["target"])),
            "dependency or target lost distinct typed local identity")
    require((doc.brep is not None, len(doc.brep_payloads)) == (payloads is not None, payloads or 0),
            "B-rep or payload status changed")
    return name, {"sha256": expected_sha, "width_id": width.id, "depth_id": depth.id,
                  "lengths_mm": values, "maps": maps, "typed_relation": proof,
                  "native_brep_payloads": len(doc.brep_payloads), "geometry_refusal": geometry_refusal}


def read_plain(managed, row):
    name, relative, expected_sha, values, payloads = row
    doc = open_read(managed / relative, expected_sha)
    parameters(doc, (18, 21), values, "driving", (), None)
    require("local_width_depth_equation" not in doc.metadata[RESOLVED]
            and doc.metadata[CONFIG]["status"] == "complete" and doc.brep is not None
            and len(doc.brep_payloads) == payloads, "plain control lost geometry or configuration compatibility")
    return name, {"sha256": expected_sha, "lengths_mm": values, "native_brep_payloads": payloads}


def read_global():
    doc = open_read(GLOBAL, GLOBAL_SHA, include_brep=False)
    (global_row,) = (param for param in doc.parameters if param.expression is not None)
    equation = global_row.expression
    require(global_row.id == "sldprt:parameter:equation:1ç5"
            and global_row.role.value == "driving" and global_row.value.value == 10.0
            and global_row.value.kind.value == "number"
            and (equation.source, equation.parameter_ids, equation.language) == ("10", (), "solidworks")
            and "local_width_depth_equation" not in doc.metadata[RESOLVED],
            "previous global assignment behavior changed")
    return {"sha256": GLOBAL_SHA, "parameter_id": global_row.id, "value": global_row.value.value,
            "expression": equation.source, "parameter_ids": equation.parameter_ids}


def cross_or_remove(link, fault):
    from convert.adapters.solidworks.Core.TypedResolved.IndexFeatures import IndexFeatures
    from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.ReadLineDims import ReadLineDims

    manager = link.ConfigValue.RootValue.FieldsValue["f9d0"]
    (row,) = manager.FieldsValue["f58"]["items"]
    relation = row["o"]
    token = relation.FieldsValue["f60"].FieldsValue["f10"]["items"][1]["o"]
    wrapper = token.FieldsValue["f80"]
    clone = wrapper.FieldsValue["f58"]
    if fault == "cross_to_actual_height":
        profile = IndexFeatures(link)[26]
        (width, height) = ReadLineDims(profile.FieldsValue["pd_f80"], link).DriverValues
        require(clone.FieldsValue["ff0"] is width.HandleValue.FieldsValue["ff0"]
                is height.HandleValue.FieldsValue["ff0"] and clone.FieldsValue["ff8"] == width.IndexValue,
                "crossing lacks the original actual width clone")
        clone.FieldsValue["ff8"] = height.IndexValue
        wrapper.FieldsValue["fb0"] = height.MetresValue
        return "local equation dimension does not alias its exact live owner"
    require(fault == "missing_local_component" and clone.FieldsValue["f58"] is not None,
            "missing-owner injection lacks the original component")
    clone.FieldsValue["f58"] = None
    return "typed model expected concrete schema one moUnitComponent_c"


def read_refusal(managed, fault):
    scope = import_module("convert.adapters.solidworks.Core.TypedResolved.Equations.TryWidthDepth")
    read_link, read_relation = scope.ReadNativeLink, scope.ReadWidthDepth
    reasons, injected = [], []

    def link_with_fault(*args, **kwargs):
        link = read_link(*args, **kwargs)
        require(kwargs["RelationConfig"] == "Default", "fault entered the wrong read branch")
        injected.append(cross_or_remove(link, fault))
        return link

    def observe_relation(*args):
        try:
            return read_relation(*args)
        except ValueError as error:
            reasons.append(str(error))
            raise

    _, relative, expected_sha, features, values, sketch, _, _, _, _ = ACTUAL[0]
    scope.ReadNativeLink, scope.ReadWidthDepth = link_with_fault, observe_relation
    try:
        doc = open_read(managed / relative, expected_sha, include_brep=False)
    finally:
        scope.ReadNativeLink, scope.ReadWidthDepth = read_link, read_relation
    require(len(injected) == 1 and reasons == injected, "normal graph refused for an unrelated reason")
    require(doc.metadata[RESOLVED]["status"] == "unsupported"
            and "local_width_depth_equation" not in doc.metadata[RESOLVED]
            and doc.metadata[CONFIG]["status"] == "unsupported", "unqualified owner was promoted")
    width, _, depth = parameters(doc, features, values, "derived", (), f'"D1@{sketch}" / 2')
    require(doc.metadata[RESOLVED]["diagnostic"] and not depth.attributes["typed_archive_owner"]
            and not width.attributes["typed_archive_owner"] and digest(managed / relative) == expected_sha,
            "lexical fallback or immutable source differs")
    return fault, {"source_sha256": expected_sha, "typed_refusal": reasons[0],
                   "public_status": "unsupported", "legacy_expression_refs": ()}


def recipe_hashes():
    graph = CORE / "TypedResolved"
    files = (
        Path(__file__).resolve(), CORE / "Adapter.py", CORE / "Native.py",
        CORE / "ConfigurationInfo.py", CORE / "ConfigGraphInfo.py", graph / "ReadNativeLink.py",
        graph / "WithTypedNative.py", *sorted((graph / "Equations").glob("*.py")),
    )
    return {str(path.relative_to(ROOT)): digest(path) for path in files}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--disclosed-root", type=Path, default=MANAGED)
    opts = parser.parse_args()
    sys.path.insert(0, str(ROOT / "src"))
    report = {
        "schema": "kit.sw2026.local-width-depth-reader.v1",
        "normal_sdk_reads": dict(read_actual(opts.disclosed_root, row) for row in ACTUAL),
        "plain_controls": dict(read_plain(opts.disclosed_root, row) for row in PLAIN),
        "legacy_global_control": read_global(),
        "typed_owner_fault_injections": dict(read_refusal(opts.disclosed_root, fault)
                                            for fault in ("cross_to_actual_height", "missing_local_component")),
        "tool_and_reader_sha256": recipe_hashes(),
        "native_execution": False,
        "heldout_inputs_read": False,
        "mutated_fixture_files": False,
    }
    print(json.dumps(report, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
