from codecs import lookup
from dataclasses import replace
from hashlib import sha256
import json
from math import isclose
from pathlib import Path, PureWindowsPath
import platform
import sys
import zlib

from BuildImportedLocalPart import batch, make_owned_nodes
from BuildLocalBodyKernel import CASES, boundary_measures, make_nodes, prism_model
from LocalBodyKernel import _render_local, decode_local, encode_closed_local, fingerprint, require
from convert.Geometry.Parasolid import DecodePartData, EncodePartData
from convert.adapters.solidworks.Archive.Partition.LocalWrite.EncodeLocalXmt import EncodeLocalXmt
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.CheckLocalBodyGraph import CheckLocalGraph
from convert.adapters.solidworks.Core.TypedResolved.Geometry.LocalBody.ReadLocalBodyNodes import ReadLocalNodes
from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit


ROOT = Path(__file__).resolve().parents[4]
ARCHIVE = "src/convert/adapters/solidworks/Archive"
PARTITION = f"{ARCHIVE}/Partition"
HOST = "re/tooling/sw2026/imported_body_source"
OWNING_SOURCES = (
    *(
        f"{PARTITION}/LocalWrite/{name}.py"
        for name in (
            "EncodeLocalXmt", "LocalXmtProfile", "WriteXmtNodeMut", "PutXmtValueMut", "GetXmtField",
            "CheckLocalXmt", "CheckXmtLink", "CheckOwnedXmt",
        )
    ),
    f"{PARTITION}/KernelShapes.py", f"{PARTITION}/SchemaHeader.py", "src/convert/Geometry/Parasolid.py",
    f"{ARCHIVE}/Construction/Part/Imports/BindImportMut.py",
    f"{ARCHIVE}/Construction/Part/EmitPartArchive.py",
    f"{HOST}/VerifyLocalXmtWriter.py", f"{HOST}/BuildImportedLocalPart.py", f"{HOST}/BuildLocalBodyKernel.py",
    f"{HOST}/LocalBodyKernel.py", "re/tooling/sw2026/para/Partition.py",
)


def package_nodes(generated):
    return tuple(XmtNode(node.index, node.kind, node.fields) for node in generated)


def compare(reference, nodes, expected):
    encoded = EncodeLocalXmt(nodes)
    require(encoded == reference, "package local transmit differs from the fresh research transmit")
    framing = EncodePartData(encoded)
    require(framing == EncodePartData(reference), "package compressed frame differs")
    wrapped, = DecodePartData(framing)
    require(wrapped.data == encoded and wrapped.stored_size == len(framing), "frame readback differs")
    packages, _ = ReadLocalNodes(encoded)
    CheckLocalGraph(packages)
    require(tuple(packages.values()) == nodes, "package reader changed generated fields")
    decoded, _ = decode_local(encoded)
    require(_render_local(decoded) == encoded, "research reader changed generated fields")
    measured = boundary_measures({node.index: node for node in decoded})
    volume, area, centroid = expected
    require(isclose(measured["volume_m3"], volume / 1e9, rel_tol=2e-12)
            and isclose(measured["area_m2"], area / 1e6, rel_tol=2e-12)
            and all(isclose(a, b / 1000, rel_tol=2e-12, abs_tol=1e-16)
                    for a, b in zip(measured["centroid_m"], centroid, strict=True)), "local body analytical measures differ")
    return {
        "raw": fingerprint(encoded),
        "frame": fingerprint(framing),
        "resident_nodes": len(packages),
        "faces": sum(node.KindValue == 14 for node in nodes),
        "edges": sum(node.KindValue == 16 for node in nodes),
        "vertices": sum(node.KindValue == 18 for node in nodes),
        "measures_si": measured,
        "raw_reference_equal": True,
        "frame_reference_equal": True,
        "typed_readback_equal": True,
    }


def change_first(nodes, kind, change):
    first = next(node for node in nodes if node.KindValue == kind)
    return tuple(change(node) if node is first else node for node in nodes)


def assign(nodes, kind, **fields):
    return change_first(nodes, kind, lambda node: replace(node, FieldsValue={**node.FieldsValue, **fields}))


def must_refuse(name, nodes, *schema):
    try:
        EncodeLocalXmt(nodes, *schema)
    except ValueError as error:
        return str(error)
    raise ValueError("unqualified transmit was accepted: " + name)


def malformed(bare, owned):
    first_edge = next(node for node in bare if node.KindValue == 16)
    other_line = next(
        node.IndexValue for node in bare if node.KindValue == 30 and node.IndexValue != first_edge.Integer("curve")
    )
    slot = next(node for node in owned if node.KindValue == 82).Indexes("values")
    names = next(node for node in owned if node.KindValue == 80).Indexes("legal_owners")
    fields = next(node for node in owned if node.KindValue == 81).Indexes("fields")
    cases = {
        "missing_field": change_first(
            bare, 12, lambda node: replace(node, FieldsValue={
                field: value for field, value in node.FieldsValue.items() if field != "body_type"
            })
        ),
        "unknown_field": assign(bare, 12, unknown_body_field=0),
        "known_but_unqualified_curve": change_first(bare, 30, lambda node: replace(node, KindValue=31)),
        "duplicate_index": change_first(bare, 16, lambda node: replace(node, IndexValue=1)),
        "absent_required_point": assign(bare, 18, point=0),
        "dangling_curve": assign(bare, 16, curve=len(bare) + 1),
        "wrong_curve_class": assign(bare, 16, curve=1),
        "foreign_curve_owner": assign(bare, 16, curve=other_line),
        "body_owner_present": assign(bare, 12, owner=1),
        "nonfinite_point": assign(bare, 29, pvec=(float("inf"), 0.0, 0.0)),
        "wrong_vector_width": assign(bare, 29, pvec=(0.0, 0.0)),
        "wrong_logical_domain": assign(owned, 70, notransmit=2),
        "bad_fixed_array": assign(owned, 80, legal_owners=names[:-1]),
        "bad_type_head_count": assign(owned, 74, n_entries=0),
        "bad_attribute_slot_count": assign(owned, 81, fields=fields + (0,)),
        "empty_owned_value": assign(owned, 98, values=()),
        "extra_integer_value": assign(owned, 82, values=slot + (1,)),
        "out_of_range_unicode_unit": assign(owned, 98, values=(1 << 16,)),
        "oversize_array": assign(owned, 98, values=(65,) * 4097),
        "oversize_node_inventory": (bare[0],) * 4097,
    }
    return {
        "alternate_schema": must_refuse("alternate_schema", bare, "SCH_3601228_36001_13006"),
        **{name: must_refuse(name, nodes) for name, nodes in cases.items()},
    }


def verify():
    lookup("utf-16-le")
    audit = BuildAudit(ROOT / "re/tooling/sw2026/serial/defs")
    audit.BeginBuild()
    enabled = True

    def guard(event, arguments):
        if enabled:
            audit.InspectEvent(event, arguments)
            if event.startswith("socket.") or event == "ctypes.dlopen":
                raise PermissionError("local transmit construction attempted " + event)

    sys.addaudithook(guard)
    try:
        cases, transmit_nodes = {}, {}
        for shape, (points, levels, expected) in CASES.items():
            model = prism_model(shape, points, levels)
            for mode, generated, render in (
                ("Bare", make_nodes(model), _render_local),
                ("Owned", make_owned_nodes(model, "Import Δ", 38, 2, 9), encode_closed_local),
            ):
                key = shape + mode
                nodes = package_nodes(generated)
                transmit_nodes[key] = nodes
                cases[key] = compare(render(generated), nodes, expected)
        refused = malformed(transmit_nodes["RectangularBare"], transmit_nodes["RectangularOwned"])
    finally:
        enabled = False
    require(not audit.DeniedReads, "local transmit construction attempted runtime access")
    require(len({case["raw"]["sha256"] for case in cases.values()}) == len(cases)
            and len({case["raw"]["bytes"] for case in cases.values()}) == len(cases),
            "shape or ownership did not affect the generated transmit")
    parts, part_reads = batch(PureWindowsPath("C:/KitPackageLocalXmt"), completed=True)
    require(set(parts) == set(cases) and not part_reads, "completed archive construction changed its scope")
    return {
        "schema": "kit.sw2026.package-local-body-transmit.v1",
        "construction_denied_io_events": len(audit.DeniedReads),
        "construction_source_file_reads": 0,
        "input_saved_part_count": 0,
        "native_application_launches": 0,
        "native_solidworks_outputs": len(parts),
        "saved_native_output_files": 0,
        "native_acceptance": False,
        "cases": cases,
        "completed_part_cases": {
            name: {"container": fingerprint(blob), "kernel": details["kernel"], "streams": details["streams"]}
            for name, (blob, details) in parts.items()
        },
        "completed_part_runtime_input_file_reads": part_reads,
        "refusals": refused,
        "owning_sources_sha256": {name: sha256((ROOT / name).read_bytes()).hexdigest() for name in OWNING_SOURCES},
        "runtime": {"python": platform.python_version(), "zlib": zlib.ZLIB_RUNTIME_VERSION},
    }


if __name__ == "__main__":
    print(json.dumps(verify(), indent=2, sort_keys=True, allow_nan=False))
