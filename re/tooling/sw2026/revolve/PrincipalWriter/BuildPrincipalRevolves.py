from argparse import ArgumentParser
from base64 import b64decode, b64encode
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from importlib import import_module
from io import BytesIO
import codecs
import json
from math import isclose, radians
from pathlib import Path, PureWindowsPath
from subprocess import check_output, run
import sys

ROOT = Path(__file__).resolve().parents[5]
REVOLVE_TOOLS = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(REVOLVE_TOOLS / "Preparation"), str(REVOLVE_TOOLS / "PrincipalReader")]

from AuditPrincipalReader import FRAMES, check_projection, digest, point, to_xyz
from MakeRevolveRequest01 import make_request
from RevolveStreamAudit02 import stream_audit

CONTROLS = (
    ("FrontFull", "front", (7, 21), (-8, 17), 2, (-13, 24), 360, 153, False),
    ("TopForward", "top", (12, 29), (-11, 16), 4, (-16, 23), 104, 171, False),
    ("TopReverse", "top", (12, 29), (-11, 16), 4, (-16, 23), 104, 171, True),
    ("RightReverse", "right", (11.3, 34.7), (-16.9, 12.2), 9.3, (-21.9, 20.2), 87.5, 138.25, True),
)
REFUSALS = {"translated-support", "rotated-support", "wrong-axis-origin", "wrong-axis-direction"}


def authored_neutral(spec, plane, alteration):
    from interchange.geometry.Models.Transform import Transform
    from interchange.geometry.Models.VectorSpace import SpaceVector

    document, _ = make_request(spec)
    frame = FRAMES[plane]
    start = point(plane, spec["axis_x_mm"], spec["axis_span_mm"][0])
    sense = -1 if spec["reverse"] else 1
    direction = tuple(sense * value for value in frame[1])
    transform = Transform(SpaceVector(0, 0, 0), *(SpaceVector(*row) for row in frame))
    if alteration == "translated-support":
        transform = replace(transform, origin=SpaceVector(1, 0, 0))
    if alteration == "rotated-support":
        transform = replace(transform, x_axis=SpaceVector(*frame[1]),
                            y_axis=SpaceVector(*(-value for value in frame[0])))
    if alteration == "wrong-axis-origin":
        start = (start[0] + 0.1, *start[1:])
    if alteration == "wrong-axis-direction":
        direction = frame[0]
    support = replace(document.support_planes[0], id=f"plane/{plane}", name=f"{plane.title()} Plane",
                      transform=transform)
    sketch = replace(document.sketches[0], support_plane_id=support.id)
    feature = document.feature_timeline[0]
    feature = replace(feature, definition=replace(feature.definition, AxisOrigin=SpaceVector(*start),
                                                  AxisDirection=SpaceVector(*direction)))
    return replace(document, support_planes=(support,), sketches=(sketch,), feature_timeline=(feature,))


def measure(raw, spec, plane):
    from convert import open_document
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
    from convert.adapters.solidworks.Core.TypedResolved.Revolves.ReadRevOwners import ReadRevOwners

    archive = SldprtArchive.from_bytes(raw)
    link = ReadNativeLink(archive, 0)
    (owner,) = ReadRevOwners(link)
    local = tuple((spec["axis_x_mm"], value) for value in spec["axis_span_mm"])
    expected_points = tuple(point(plane, *value) for value in local)
    for vector, expected in zip((owner.FrameValue.StartValue, owner.FrameValue.EndValue),
                                expected_points, strict=True):
        assert all(isclose(value, target, abs_tol=1e-12) for value, target in zip(to_xyz(vector), expected, strict=True))
    assert to_xyz(owner.FrameValue.RawDirection) == FRAMES[plane][1]
    assert owner.IsReverse == spec["reverse"]
    stream_result, history = stream_audit(archive, link)
    assert len(stream_result) == 8 and len(history) == 2 and all(row["qualified"] for row in history.values())
    document = open_document(raw, source_format="solidworks.sldprt", strict=True)
    reference = owner.ProfileValue.FieldsValue["pd_f78"]
    assert reference.ClassValue.NameValue == "moCompRefPlane_c"
    assert reference.FieldsValue["f100"] == {"front": 3, "top": 2, "right": 1}[plane]
    plane_id = reference.FieldsValue["ff0"]["f00"]
    (axis,) = [entity for entity in document.sketches[0].entities if entity.construction]
    observed = tuple((point_value.x, point_value.y) for point_value in (axis.geometry.start, axis.geometry.end))
    for pair, wanted in zip(observed, local, strict=True):
        assert all(isclose(value, target, abs_tol=1e-12) for value, target in zip(pair, wanted, strict=True))
    projection = check_projection(document, plane, plane_id, observed, radians(spec["angle_deg"]), spec["reverse"])
    assert document.brep is not None and len(document.brep.bodies) == len(document.bodies) == 1
    assert not document.brep_payloads
    (body,) = document.bodies
    assert (body.topology.solid_count, body.topology.shell_count, body.topology.face_count) == (
        1, 1, 4 if spec["angle_deg"] == 360 else 6,
    )
    return {
        "projection": projection, "archive_streams": stream_result | history,
        "body_faces": body.topology.face_count, "volume_mm3": body.topology.volume,
        "area_mm2": body.topology.surface_area,
    }


def worker(request):
    from convert.adapters.base.WriteOptions import WriteOptions
    from convert.adapters.solidworks.Core.Preparation.Revolve.CanPrepRevolve import CanPrepRevolve
    from convert.adapters.solidworks.Core.Preparation.Revolve.PrepareRevolve import PrepareRevolve

    for encoding in ("ascii", "utf-8", "utf-8-sig", "utf-16-le", "utf-16-be", "latin-1"):
        codecs.lookup(encoding)
    for module in (
        "interchange.document.Models.DocumentProvenance",
        "interchange.document.Validation.AngleRevValidate",
        "interchange.document.Validation.DocumentAssemblyValidate",
        "interchange.document.Validation.DocumentFeatureValidate",
        "interchange.document.Validation.DocumentReferenceValidate",
        "interchange.document.Validation.PlaneRevValidate",
        "interchange.document.Validation.DistExtValidate",
    ):
        import_module(module)
    denied = []
    guarding = True

    def audit(event, args):
        if guarding and (event == "open" or event.startswith(("subprocess.", "socket."))
                         or event in ("os.listdir", "os.scandir", "os.system", "os.fork", "os.posix_spawn", "ctypes.dlopen")):
            denied.append(event)
            raise RuntimeError(f"revolve preparation attempted external access: {event}")

    spec, plane = request["spec"], request["plane"]
    change = request.get("alteration")
    assert change is None or change in REFUSALS
    path = spec["self_path"]
    epoch = spec["created_at"]
    sys.addaudithook(audit)
    try:
        document = authored_neutral(spec, plane, change)
        options = WriteOptions(configuration=document.configurations[0].id)
        stream = BytesIO()
        stream_options = WriteOptions(configuration=document.configurations[0].name,
                                      values={"final_destination": path})
        if change:
            assert not CanPrepRevolve(document, stream, epoch, stream_options)
            try:
                PrepareRevolve(document, stream, epoch, stream_options)
            except (ValueError, TypeError) as error:
                assert not stream.getvalue()
                return None, {"refusal": str(error), "external_access_attempts": denied}
            raise ValueError("unsupported frame or selected axis was admitted")
        assert CanPrepRevolve(document, path, epoch, options)
        assert CanPrepRevolve(document, stream, epoch, stream_options)
        direct = PrepareRevolve(document, path, epoch, options)
        streamed = PrepareRevolve(document, stream, epoch, stream_options)
        assert not stream.getvalue() and direct.BytesValue == streamed.BytesValue
        assert direct.InputValue.OutputValue.PathName == streamed.InputValue.OutputValue.PathName == path
    finally:
        guarding = False
    assert not denied
    raw = direct.BytesValue
    proof = measure(raw, spec, plane)
    return raw, {
        "sha256": digest(raw), "bytes": len(raw), "external_access_attempts": denied,
        "path_and_named_stream_equal": True, "caller_stream_untouched": True, **proof,
    }


def encode(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def run_worker(request):
    child = run((sys.executable, "-I", "-B", __file__, "--worker"), input=encode(request),
                capture_output=True, check=False, timeout=100)
    if child.returncode or child.stderr:
        raise ValueError(f"{request['spec']['name']} {request.get('alteration', '')}: {child.stderr.decode()}")
    reply = json.loads(child.stdout)
    raw = b64decode(reply.pop("output"), validate=True)
    assert not reply["external_access_attempts"]
    if raw:
        assert digest(raw) == reply["sha256"] and len(raw) == reply["bytes"]
    return raw, reply


def requests(guest):
    for suffix, plane, radius, axial, axis, span, angle, edit, reverse in CONTROLS:
        name = "KitPrincipalRevolve" + suffix
        yield {"plane": plane, "spec": {
            "name": name, "radial_mm": radius, "axial_mm": axial, "axis_x_mm": axis,
            "axis_span_mm": span, "angle_deg": angle, "reverse": reverse, "edit_angle_deg": edit,
            "created_at": 1760000000, "self_path": str(guest / f"{name}.SLDPRT"),
        }}


def main(output, guest):
    assert output.is_absolute() and output.is_dir() and not output.is_relative_to(ROOT)
    assert guest.is_absolute() and not any(output.iterdir())
    revision = check_output(("git", "rev-parse", "HEAD"), cwd=ROOT, text=True).strip()
    source_tree = check_output(("git", "rev-parse", "HEAD:src"), cwd=ROOT, text=True).strip()
    positives = list(requests(guest))
    negatives = [positives[1 + (index % 2)] | {"alteration": change}
                 for index, change in enumerate(sorted(REFUSALS))]
    all_requests = positives + negatives
    with ThreadPoolExecutor(max_workers=4) as pool:
        built = list(pool.map(run_worker, all_requests))
    records = []
    for request, (raw, proof) in zip(all_requests, built, strict=True):
        if raw:
            candidate = output / PureWindowsPath(request["spec"]["self_path"]).name
            with candidate.open("xb") as stream:
                stream.write(raw)
        records.append({"request": request, "proof": proof})
    capture = encode({
        "schema": "kit.sw2026.sdk-principal-revolve-discovery.v1", "source_revision": revision,
        "source_tree": source_tree, "tool_sha256": digest(Path(__file__).read_bytes()),
        "cases": records, "sealed_sources_read": 0, "native_processes": 0,
    })
    (output / "Build.json").write_bytes(capture)
    print(json.dumps({"guarded_processes": len(records), "generated_candidates": len(positives),
                      "receipt_sha256": digest(capture)}))


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--guest", type=PureWindowsPath)
    args = parser.parse_args()
    if args.worker:
        payload, report = worker(json.load(sys.stdin))
        print(json.dumps(report | {"output": b64encode(payload or b"").decode("ascii")}, allow_nan=False))
    else:
        main(args.output, args.guest)
