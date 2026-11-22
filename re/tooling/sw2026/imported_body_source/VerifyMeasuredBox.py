from argparse import ArgumentParser
from codecs import lookup
from contextlib import contextmanager
from dataclasses import replace
from hashlib import sha256
from io import BytesIO
from itertools import product
import json
from math import isclose
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from zlib import ZLIB_RUNTIME_VERSION

ROOT = Path(__file__).resolve().parents[4]
sys.path[:0] = [str(ROOT / "src"), str(ROOT)]

from convert import open_document, write_document
from convert.Geometry.Extrude.Polygon.PolygonExtrude import BuildPrism
from convert.Geometry.Revolve.SweepVector import CrossVector, DotVector
from convert.adapters.base.TransferContract import TransferMode
from convert.adapters.base.WritePolicy import GetDocumentCaps
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.registry.RegistryErrors import NotFoundError
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeader
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.Preparation.Imports.PrepareImport import PrepareImport
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.adapters.solidworks.Core.Writing.SldprtWriter import SldprtWriter
from interchange import Capability, CadDocument, CadSource, Configuration
from interchange.geometry.Models.GeometryCurves import LineGeometry
from interchange.geometry.Models.Transform import KTransformIdentity
from interchange.geometry.Models.VectorPlane import PlaneVector
from tests.Convert.Solidworks.PlainWriting.MeasurePlainDoc import MeasurePlainDoc

RECEIPT = ROOT / "re/solidworks/measurements/2026/GeneratedLocalBodyPartCompleted01.json"
REFERENCE = ROOT / "re/solidworks/v2026/corpus/local-import-readback/RectangularBare.SLDPRT"
RECEIPT_SHA = "40d77a01a37e8d85517fbfa642a208bdcd3b29378d426021b643cbd909e1a6c4"
LOCATOR = r"C:\KitImportedProbe03\Candidates\RectangularBare.SLDPRT"
FORMAT = "solidworks.sldprt"
EPOCH = 1790000000
BOUNDS = ((-9.0, 4.0), (5.0, 23.0), (3.0, 14.0))
CAPABILITIES = {"brep", "configurations"}


def require(value, message):
    if not value:
        raise ValueError(message)


def fingerprint(data):
    return {"bytes": len(data), "sha256": sha256(data).hexdigest()}


def prism(outline, stations, configuration="Default"):
    points = tuple(PlaneVector(*point) for point in outline)
    lines = tuple(LineGeometry(a, b) for a, b in zip(points, points[1:] + points[:1], strict=True))
    model, *_ = BuildPrism("import-witness", KTransformIdentity, lines, *stations)
    body, = model.bodies
    return CadDocument(
        CadSource("kit.neutral", "", ""), (Configuration("active", configuration, True),),
        (), (), (), (), (), (), brep=replace(model, bodies=(replace(body, design_body_id=""),)),
    )


def box(bounds):
    (left, right), (front, back), stations = bounds
    return prism(((left, front), (right, front), (right, back), (left, back)), stations)


@contextmanager
def guard():
    watched = {
        "open", "os.listdir", "os.scandir", "os.system", "os.exec", "os.posix_spawn",
        "os.spawn", "os.fork", "os.forkpty", "os.startfile",
    }
    active = True
    touches = []

    def observe(event, args):
        if active and (
            event in watched or event.startswith(("ctypes.", "subprocess.", "socket.", "winreg."))
            or event == "import" and args[0].split(".")[0] in {
                "FreeCAD", "pythoncom", "win32com", "comtypes", "adsk",
            }
        ):
            touches.append(event)
            raise RuntimeError("model processing attempted external access: " + event)

    sys.addaudithook(observe)
    try:
        yield touches
    finally:
        active = False
    require(not touches, "guard observed an external access")


def ring_points(model, loop):
    vertices = {row.id: row.point for row in model.vertices}
    edges = {row.id: row for row in model.edges}
    coedges = {row.id: row for row in model.coedges}
    pairs = []
    for key in loop.coedge_ids:
        use = coedges[key]
        edge = edges[use.edge_id]
        ends = (edge.start_vertex_id, edge.end_vertex_id)
        pairs.append(ends[::-1] if use.reversed else ends)
    require(len(pairs) == 4 and all(
        end == start for (_, end), (start, _) in zip(pairs, pairs[1:] + pairs[:1], strict=True)
    ), "box faces need four consistently oriented edge links")
    return tuple(vertices[start] for start, _ in pairs)


def moments(model):
    triangles = []
    for loop in model.loops:
        first, *ring = ring_points(model, loop)
        for second, third in zip(ring[:-1], ring[1:], strict=True):
            sides = tuple(
                replace(second, x=point.x-first.x, y=point.y-first.y, z=point.z-first.z)
                for point in (second, third)
            )
            normal = CrossVector(*sides)
            area = (normal.x**2 + normal.y**2 + normal.z**2)**0.5 / 2
            vol6 = DotVector(first, CrossVector(second, third))
            moment = tuple(sum(getattr(p, axis) for p in (first, second, third))*vol6 for axis in "xyz")
            triangles.append((vol6, area, moment))
    six_volume = sum(value[0] for value in triangles)
    area = sum(value[1] for value in triangles)
    require(six_volume > 0, "signed measured volume is not outward")
    centroid = tuple(sum(value[2][axis] for value in triangles) / (4*six_volume) for axis in range(3))
    return (six_volume/6, area, centroid)


def read_back(payload, case):
    archive = SldprtArchive.from_bytes(payload)
    linked = ReadNativeLink(archive, 0)
    feature, = (row for row in linked.ResolvedValue.RootsValue
                if row is not None and row.ClassValue.NameValue == "moBaseBody_c")
    root = linked.ConfigValue.RootValue
    atom, = root.FieldsValue["fd88"]["atoms"]
    require(feature.FieldsValue["f528"]["items"][0]["o"] is atom["o"]
            and feature.FieldsValue["f498"] == [{"v": atom["o"].FieldsValue["f140"]}]
            and feature.FieldsValue["f3d0"].FieldsValue["f18"] > root.FieldsValue["fe38"].FieldsValue["f18"],
            "typed owner lost its shared atom and distinct marks")
    for path in ("Header2", "Contents/Config-0-ModelHeader"):
        require(ReadHeader(archive.require(path), 19000).SelfFile.PathValue == LOCATOR,
                "generated headers lost their modeled self locator")
    doc = open_document(payload, source_format=FORMAT, strict=True)
    shape = doc.brep
    body, = doc.bodies
    imported, = (row for row in doc.feature_timeline if row.kind == "imported")
    config, = doc.configurations
    require(not doc.validate() and config.active and config.name == "Default"
            and body.final_feature_id == imported.id == f"sldprt:feature:{feature.FieldsValue['f08']}"
            and imported.name == body.name == "Imported geometry"
            and shape.bodies[0].design_body_id == body.id and not doc.parameters,
            "public read lost the selected imported body or invented editable history")
    observed = {tuple(getattr(vertex.point, axis) for axis in "xyz") for vertex in shape.vertices}
    normals = {tuple(getattr(surface.normal, axis) for axis in "xyz") for surface in shape.surfaces}
    expected_normals = {tuple(sign if i == axis else 0 for i in range(3))
                        for axis, sign in product(range(3), (-1, 1))}
    counts = [len(value) for value in (shape.bodies, shape.shells, shape.faces, shape.edges, shape.vertices)]
    require(observed == set(product(*BOUNDS)) and normals == expected_normals
            and counts == [1, 1, 6, 12, 8], "public reader changed the exact oriented box boundary")
    volume, area, centroid = moments(shape)
    native = case["geometry"]
    pairs = ((volume*1e-9, native["volume_m3"]), (area*1e-6, native["area_m2"]),
             *((a*1e-3, b) for a, b in zip(centroid, native["com_m"], strict=True)))
    require(all(isclose(a, b, rel_tol=1e-12) for a, b in pairs),
            "independent signed B-rep integration disagrees with the native measurements")
    design = open_document(payload, source_format=FORMAT, strict=True, include_brep=False)
    metadata_body, = design.bodies
    require(design.brep is None and not design.brep_payloads
            and (metadata_body.id, metadata_body.final_feature_id) == (body.id, body.final_feature_id)
            and any(row.id == imported.id and row.name == imported.name for row in design.feature_timeline),
            "design-only strict read changed actual imported feature identity")
    return {"topology": counts, "volume_mm3": volume, "area_mm2": area, "centroid_mm": centroid,
            "feature_id": feature.FieldsValue["f08"], "atom_id": atom["o"].FieldsValue["f140"],
            "design_only_body_name": metadata_body.name}


def assert_result(result):
    require(result.vendor_loadable and result.application_usable and not result.dropped
            and {row.capability.value for row in result.transfers} == CAPABILITIES
            and all(row.mode is TransferMode.KNative for row in result.transfers),
            "publication did not report the two actual native transfers")
    warning, = result.diagnostics
    require(warning.code == "sldprt.parametric_history_unavailable"
            and warning.attributes["capability"] == "parametric_history",
            "public result did not disclose the native history boundary")


def refuse(action, errors, text):
    try:
        action()
    except errors as error:
        require(text in str(error), f"wrong refusal for {text}: {error}")
        return text
    raise ValueError("unmeasured input reached publication: " + text)


def verify_refusals(document, options, varied, plain):
    stream = BytesIO(b"caller-owned destination")
    stream.seek(4)
    writer = SldprtWriter()
    publish = lambda doc, values: write_document(doc, stream, destination_format=FORMAT,
                                                allow_carrier=True, values=values)
    case = options["solidworks_native_measurement"]
    good_report = case["receipt"]
    tampered = options | {"solidworks_native_measurement": case | {
        "receipt": good_report | {"controls_healthy": False},
    }}
    requests = {
        "missing_receipt": (lambda: publish(document, {"final_destination": LOCATOR}),
                            ValueError, "requires an offline native measurement"),
        "altered_receipt": (lambda: publish(document, tampered),
                            ValueError, "requires its exact controlled native receipt"),
        "changed_geometry": (lambda: publish(varied, options),
                            ValueError, "no exact native measurement"),
        "wrong_locator": (lambda: publish(document, options | {"final_destination":
                           LOCATOR.replace("Candidates", "Different")}),
                          ValueError, "no exact native measurement"),
        "other_epoch": (lambda: publish(document, options | {"solidworks_native_measurement":
                            case | {"written_at": EPOCH + 1}}),
                       ValueError, "no exact native measurement"),
        "source_metadata": (lambda: publish(replace(document, metadata={"unmodeled": True}), options),
                            NotFoundError, "does not support the destination"),
        "declared_history": (lambda: publish(replace(
            document, capabilities=frozenset((Capability.KParamHistory,))), options),
                            NotFoundError, "does not support the destination"),
        "existing_editable_history": (lambda: publish(replace(plain, brep=document.brep), options),
                                      NotFoundError, "does not support the destination"),
        "registry_nonempty_stream": (lambda: publish(document, options),
                                     ValueError, "standalone"),
        "direct_nonempty_stream": (lambda: writer.write(document, stream, WriteOptions(values=options)),
                                   ValueError, "standalone"),
        "same_counts_trapezoid": (lambda: publish(prism(((-9, 5), (4, 5), (7, 23), (-9, 23)), (3, 14)), options),
                                  NotFoundError, "does not support the destination"),
    }
    results = {key: refuse(action, errors, message) for key, (action, errors, message) in requests.items()}
    require(stream.getvalue() == b"caller-owned destination" and stream.tell() == 4,
            "a rejected write modified somebody else's stream")
    return results


def path_refusals(document, options):
    with TemporaryDirectory(prefix="kit-import-refuse-") as scratch:
        target = Path(scratch) / "RectangularBare.SLDPRT"
        target.write_bytes(b"preserve existing destination")
        writer = SldprtWriter()
        result = refuse(lambda: writer.write(document, target, WriteOptions(overwrite=True, values=options)),
                        ValueError, "actual measured Windows destination")
        original = target.read_bytes()
        require(original == b"preserve existing destination" and len(list(target.parent.iterdir())) == 1,
                "a wrong asserted physical locator modified its destination")
        untouched = target.parent / "missing" / target.name
        refuse(lambda: write_document(document, untouched, destination_format=FORMAT, values=options),
               ValueError, "actual measured Windows destination" if sys.platform != "win32"
               else "no exact native measurement")
        require(not untouched.parent.exists(), "refused path left its stage or directory")
    return {"direct": result, "registry_untouched": True}


def check_compression(generated, reference):
    generated_streams = SldprtArchive.from_bytes(generated).streams
    disclosed_streams = SldprtArchive.from_bytes(reference).streams
    kernel_owners = {"Config-0-FeatureBodies/LocalBodies", "Contents/Config-0-Partition"}
    require(set(generated_streams) == set(disclosed_streams)
            and all(generated_streams[name] == disclosed_streams[name]
                    for name in disclosed_streams.keys() - kernel_owners),
            "alternate compression changed the linked logical archive")
    expected = open_document(reference, source_format=FORMAT, strict=True).brep_payloads
    actual = open_document(generated, source_format=FORMAT, strict=True).brep_payloads
    require(len(expected) == len(actual) == 3
            and all((a.kind, a.source_stream, a.data) == (b.kind, b.source_stream, b.data)
                    for a, b in zip(actual, expected, strict=True)),
            "alternate compression changed the raw kernel bodies or history")



def check(coverage_only=False):
    for codec in ("ascii", "latin-1", "cp1252", "utf-8", "utf-16-le", "utf-16-be"):
        lookup(codec)
    raw_receipt, reference = RECEIPT.read_bytes(), REFERENCE.read_bytes()
    require(sha256(raw_receipt).hexdigest() == RECEIPT_SHA, "offline receipt changed")
    receipt = json.loads(raw_receipt)
    case = receipt["cases"]["RectangularBare"]
    require(fingerprint(reference) == {"bytes": case["generated_bytes"], "sha256": case["native_input_sha256"]},
            "independent native-tested fixture changed")
    options = {"final_destination": LOCATOR,
               "solidworks_native_measurement": {"written_at": EPOCH, "receipt": receipt}}
    document = CadDocument.from_json(box(BOUNDS).to_json())
    previous = {role: MeasurePlainDoc(role) for role in ("Skew", "Step")}
    GetDocumentCaps(document)
    varied = box(((-9.5, 4.0), (5.0, 23.0), (3.0, 14.0)))
    with guard() as touches:
        prepared = PrepareImport(document, BytesIO(), EPOCH, WriteOptions(values=options))
        expected = fingerprint(reference)
        matches = fingerprint(prepared.BytesValue) == expected
        if coverage_only and not matches and "zlib-ng" in ZLIB_RUNTIME_VERSION:
            require(len(prepared.StreamsValue) == 12, "archive changed its logical stream inventory")
            stream = BytesIO()
            refusal = refuse(lambda: write_document(document, stream, destination_format=FORMAT, values=options),
                             ValueError, "no exact native measurement")
            require(stream.getvalue() == b"", "unmeasured compressor output reached a stream")
            comparison = {"exact_publications": 0, "unmatched_compressor": ZLIB_RUNTIME_VERSION,
                          "distinct_compression_refused": refusal}
        else:
            comparison = {}
    if comparison:
        check_compression(prepared.BytesValue, reference)
        return {"passed": True, **comparison, "readback": read_back(prepared.BytesValue, case),
                "runtime_external_events": len(touches)}
    with guard() as additional:
        require(matches and prepared.BytesValue == reference, "prepared archive differs from exact native input")
        require({name: fingerprint(data) for name, data in prepared.StreamsValue.items()}
                == case["generated_streams"], "prepared logical streams differ from exact measured input")
        direct = BytesIO()
        assert_result(SldprtWriter().write(document, direct, WriteOptions(values=options)))
        staged = BytesIO()
        assert_result(write_document(document, staged, destination_format=FORMAT,
                                     allow_carrier=False, values=options))
        require(direct.getvalue() == staged.getvalue() == prepared.BytesValue,
                "public publishers did not emit the same standalone archive")
        legacy_digests = {}
        for role, (plain, plain_receipt, plain_digest) in previous.items():
            history = BytesIO()
            legacy = write_document(plain, history, destination_format=FORMAT, values={
                "final_destination": f"C:\\KitSdkCandidates\\{plain.metadata['name']}.SLDPRT",
                "solidworks_native_measurement": plain_receipt,
            })
            require(legacy.application_usable and fingerprint(history.getvalue())["sha256"] == plain_digest,
                    "plain editable archive changed or stopped publishing")
            legacy_digests[role] = plain_digest
        refusals = verify_refusals(document, options, varied, previous["Skew"][0])
        other = PrepareImport(varied, BytesIO(), EPOCH, WriteOptions(values=options))
    readback = read_back(staged.getvalue(), case)
    varied_read = open_document(other.BytesValue, source_format=FORMAT)
    require(any(vertex.point.x == -9.5 for vertex in varied_read.brep.vertices),
            "unmeasured control must retain the changed endpoint")
    return {"passed": True, "archive": expected, "exact_publications": 2,
            "exact_streams": len(prepared.StreamsValue), "native_receipt_sha256": RECEIPT_SHA,
            "readback": readback, "refusals": refusals, "path_refusals": path_refusals(document, options),
            "previous_plain_sha256": legacy_digests, "runtime_external_events": len(touches) + len(additional),
            "native_processes_started": 0, "heldout_cases": 0}


if __name__ == "__main__":
    parser = ArgumentParser(description="Verify measured rectangular solid publication without a CAD runtime")
    parser.add_argument("--remote-coverage", action="store_true")
    arguments = parser.parse_args()
    print(json.dumps(check(arguments.remote_coverage), indent=2, sort_keys=True, allow_nan=False))
