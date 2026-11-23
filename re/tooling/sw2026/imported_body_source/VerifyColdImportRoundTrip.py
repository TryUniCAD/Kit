from codecs import lookup
from contextlib import contextmanager
from dataclasses import replace
from hashlib import sha256
from importlib import import_module
from io import BytesIO
import json
from math import isclose
from pathlib import Path
import sys
from zlib import ZLIB_RUNTIME_VERSION

ROOT = Path(__file__).resolve().parents[4]
sys.path[:0] = [str(ROOT / "src"), str(ROOT)]

from convert import open_document, write_document
from convert.adapters.base.GetDocumentCaps import GetDocumentCaps
from convert.adapters.base.TransferContract import TransferMode
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.registry.RegistryErrors import RegistryError
from convert.adapters.solidworks.Archive.Header.ReadFileTable import GetFileRef
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.Adapter import SldprtAdapter
from convert.adapters.solidworks.Core.Preparation.Imports.PrepareImport import PrepareImport
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.adapters.solidworks.Core.Writing.SldprtWriter import SldprtWriter
from interchange.document.Models.DocumentModel import CadDocument

FORMAT = "solidworks.sldprt"
FOLDER = ROOT / "re/solidworks/v2026/corpus/local-import-readback"
RECEIPT = ROOT / "re/solidworks/measurements/2026/GeneratedLocalBodyPartCompleted01.json"
RECEIPT_SHA = "40d77a01a37e8d85517fbfa642a208bdcd3b29378d426021b643cbd909e1a6c4"
KERNEL_OWNERS = {"Config-0-FeatureBodies/LocalBodies", "Contents/Config-0-Partition"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def fingerprint(payload):
    return {"bytes": len(payload), "sha256": sha256(payload).hexdigest()}


@contextmanager
def guard():
    for module in ("document.Models.DocumentProvenance", "document.Validation.DocumentValidate",
                   "document.Validation.DocumentAssemblyValidate", "document.Validation.DocumentFeatureValidate",
                   "document.Validation.DocumentReferenceValidate", "document.Behavior.DocumentIo",
                   "brep.Validation.BrepValidate"):
        import_module("interchange." + module)
    for codec in ("ascii", "latin-1", "cp1252", "utf-8", "utf-16-le", "utf-16-be"):
        lookup(codec)
    events = []
    active = True

    def observe(event, args):
        if active and (
            event in {"open", "os.listdir", "os.scandir", "os.system", "os.exec", "os.posix_spawn",
                      "os.spawn", "os.fork", "os.forkpty", "os.startfile"}
            or event.startswith(("ctypes.", "subprocess.", "socket.", "winreg."))
            or event == "import" and args[0].split(".")[0] in {"win32com", "pythoncom", "FreeCAD", "Part", "adsk"}
        ):
            events.append(event)
            raise RuntimeError("import round trip attempted external access: " + event)

    sys.addaudithook(observe)
    try:
        yield events
    finally:
        active = False
    require(not events, "runtime accessed an external resource")


def cross(left, right):
    return (left[1] * right[2] - left[2] * right[1],
            left[2] * right[0] - left[0] * right[2],
            left[0] * right[1] - left[1] * right[0])


def xyz(value):
    return value.x, value.y, value.z


def dot(left, right):
    return sum(a * b for a, b in zip(left, right, strict=True))


def check_geometry(document, measured):
    model = document.brep
    require(model is not None and not model.validate(frozenset(body.id for body in document.bodies)),
            "strict import lost its finite boundary")
    root, = model.bodies
    body, = document.bodies
    require(root.design_body_id == body.id and len(model.regions) == 1
            and model.regions[0].solid, "strict import lost its sole solid producer")
    expected = measured["geometry"]
    require((len(model.faces), len(model.edges), len(model.vertices))
            == (expected["faces"], expected["edges"], expected["vertices"]), "native topology counts changed")
    vertices = {row.id: xyz(row.point) for row in model.vertices}
    edges = {row.id: row for row in model.edges}
    coedges = {row.id: row for row in model.coedges}
    surfaces = {row.id: row for row in model.surfaces}
    face_normals = {row.loop_ids[0]: xyz(surfaces[row.surface_id].normal) for row in model.faces}
    volume6 = 0.0
    area = 0.0
    moment = [0.0, 0.0, 0.0]
    for loop in model.loops:
        ring = []
        for key in loop.coedge_ids:
            use = coedges[key]
            edge = edges[use.edge_id]
            ring.append(vertices[edge.end_vertex_id if use.reversed else edge.start_vertex_id])
        first, *rest = ring
        for second, third in zip(rest[:-1], rest[1:], strict=True):
            vol = dot(first, cross(second, third))
            volume6 += vol
            moment = [value + (a + b + c) * vol
                      for value, a, b, c in zip(moment, first, second, third, strict=True)]
            ab = tuple(b - a for a, b in zip(first, second, strict=True))
            ac = tuple(c - a for a, c in zip(first, third, strict=True))
            area += dot(cross(ab, ac), face_normals[loop.id]) / 2
    actual = (volume6 / 6e9, area / 1e6, *(value / (4000 * volume6) for value in moment))
    target = (expected["volume_m3"], expected["area_m2"], *expected["com_m"])
    require(all(isclose(a, b, rel_tol=1e-10, abs_tol=1e-15) for a, b in zip(actual, target, strict=True)),
            "neutral solid volume, area or centre differs from the controlled native result")


def publish(route, document, target, options):
    if route == "registry":
        return write_document(document, target, destination_format=FORMAT, allow_carrier=False, values=options)
    if route == "writer":
        return SldprtWriter().write(document, target, WriteOptions(values=options))
    return SldprtAdapter().write(document, target, WriteOptions(values=options))


def refuse(route, document, options, message=None):
    target = BytesIO(b"untouched")
    try:
        publish(route, document, target, options)
    except (ValueError, TypeError, RegistryError) as error:
        require(message is None or message in str(error), "unexpected refusal: " + str(error))
    else:
        raise ValueError("unsupported import reached publication")
    require(target.getvalue() == b"untouched", "refusal modified the stream")


def variants(document):
    source = replace(document.source, sha256="0" * 64)
    model = document.brep
    vertex, *rest = model.vertices
    bad_geometry = replace(model, vertices=(replace(vertex, tolerance=1e-7), *rest))
    return (
        replace(document, source=source),
        replace(document, metadata=dict(document.metadata) | {"foreign": "part property"}),
        replace(document, metadata=dict(document.metadata) | {"solidworks_source_bytes": b"changed witness"}),
        replace(document, brep_payloads=()),
        replace(document, brep=bad_geometry),
    )


def check_case(role, receipt):
    path = FOLDER / (role + ".SLDPRT")
    original = path.read_bytes()
    case = receipt["cases"][role]
    identity = fingerprint(original)
    require(identity == {"bytes": case["generated_bytes"], "sha256": case["native_input_sha256"]},
            "native-tested archive identity changed")
    archive = SldprtArchive.from_bytes(original)
    linked = ReadNativeLink(archive, 0)
    header = linked.ConfigValue.HeaderValue.FieldsValue
    options = {"final_destination": GetFileRef(header["f38"]).PathValue,
               "solidworks_native_measurement": {"written_at": header["f70"], "receipt": receipt}}
    strict = open_document(original, source_format=FORMAT, strict=True)
    linked_path = open_document(path, source_format=FORMAT, strict=True)
    roundtrip = CadDocument.from_json(linked_path.to_json())
    design = open_document(original, source_format=FORMAT, strict=True, include_brep=False)
    (full_body,) = strict.bodies
    (design_body,) = design.bodies
    require(design.brep is None and not design.brep_payloads
            and (design_body.id, design_body.name, design_body.final_feature_id)
            == (full_body.id, full_body.name, full_body.final_feature_id)
            and design.metadata["solidworks.native_body_names"] == strict.metadata["solidworks.native_body_names"],
            "design-only local import lost its measured name or body owner")
    check_geometry(strict, case)
    check_geometry(roundtrip, case)
    negative = variants(strict)
    bad_options = dict(options) | {
        "solidworks_native_measurement": {"written_at": header["f70"] + 1, "receipt": receipt},
    }
    routes = ("registry", "writer", "adapter")
    with guard() as events:
        candidate = PrepareImport(strict, BytesIO(), header["f70"], WriteOptions(values=options))
        streams = candidate.StreamsValue
        expected = archive.streams
        require(set(streams) == set(expected), "local import changed its stream inventory")
        exact = candidate.BytesValue == original
        if exact:
            require({name: fingerprint(data) for name, data in streams.items()} == case["generated_streams"],
                    "computed streams differ from the measured archive")
            for document in (strict, roundtrip):
                for route in routes:
                    target = BytesIO()
                    result = publish(route, document, target, options)
                    require(target.getvalue() == original and result.vendor_loadable and result.application_usable,
                            "public writer changed the native-tested container")
                    require({entry.CapabilityData for entry in result.Transfers} == GetDocumentCaps(document)
                            and all(entry.TransferModeData is TransferMode.KNative for entry in result.Transfers),
                            "exact imported-solid transfer lost a source capability")
            for document in negative:
                for route in routes:
                    refuse(route, document, options)
        else:
            require("zlib-ng" in ZLIB_RUNTIME_VERSION
                    and all(streams[name] == expected[name] for name in set(expected) - KERNEL_OWNERS),
                    "import archive changed outside known compressor framing")
            alternate = open_document(candidate.BytesValue, source_format=FORMAT, strict=True)
            check_geometry(alternate, case)
            require([(row.source_stream, row.kind, row.data) for row in strict.brep_payloads]
                    == [(row.source_stream, row.kind, row.data) for row in alternate.brep_payloads],
                    "alternate compression changed decoded physical kernel content")
            for document in (strict, roundtrip):
                for route in routes:
                    refuse(route, document, options, "no exact native measurement")
        for route in routes:
            refuse(route, design, options)
            refuse(route, strict, bad_options, "no exact native measurement")
    return {"archive": identity, "generated": fingerprint(candidate.BytesValue),
            "logical_streams": len(streams), "exact_writes": 6 if exact else 0,
            "refusals": 21 if exact else 12, "geometry_comparisons": 10 if exact else 15,
            "runtime_reads": len(events)}


def main():
    data = RECEIPT.read_bytes()
    require(sha256(data).hexdigest() == RECEIPT_SHA, "native import receipt changed")
    receipt = json.loads(data)
    cases = {role: check_case(role, receipt) for role in ("RectangularBare", "ConcaveOwned")}
    print(json.dumps({"passed": True, "cases": cases, "compressor": ZLIB_RUNTIME_VERSION,
                      "native_processes_started": 0, "native_receipt_sha256": RECEIPT_SHA,
                      "new_held_out_cases": 0, "fcstd_conversions": 0}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
