from argparse import ArgumentParser
from codecs import lookup
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

TARGET = r"C:\KitEncoderRoundTrip\reconstruction.SLDPRT"
EPOCH = 1785626030
EDIT_MM = 19.87


def setup(root):
    sys.path[:0] = [str(root / "src"), str(root / "re"), str(root / "re/automation")]


def authored_request(neutral, unit, value):
    from interchange.document.Models.DocumentModel import CadDocument
    from interchange.Records.RecordSource import CadSource

    document = CadDocument.from_json(neutral.decode("utf-8"))
    driver, = document.parameters
    boss, = document.feature_timeline
    length = replace(driver.value, value=value, unit=unit)
    return replace(
        document,
        source=CadSource("kit.neutral", "<authored depth unit contrast>", sha256(neutral).hexdigest()),
        parameters=(replace(driver, value=length),),
        feature_timeline=(replace(boss, definition=replace(boss.definition, length=length)),),
    )


def edit_and_emit(root, request):
    setup(root)
    from EncoderRoundTrip.Solidworks import generate_prepared_candidate, prepare_generation_input
    from EncoderRoundTrip.Source import decode_writer_input, encode_writer_input
    from convert import open_document
    from convert.adapters.solidworks.Core.Preparation.PlanPartWrite import PlanPartWrite
    from interchange.document.Models.DocumentModel import CadDocument

    document = CadDocument.from_json(request["source_json"])
    before = encode_writer_input(document)
    requested_unit = request["source_unit"]
    original = document.parameters[0].value
    if original.unit != requested_unit or document.units != "mm":
        raise ValueError("persisted contrast lost the explicit source length or document unit")
    for codec in ("ascii", "latin-1", "cp1252", "utf-8", "utf-16-le", "utf-16-be"):
        lookup(codec)
    active = True
    denied = []

    def audit(event, _):
        if active and (
            event in (
                "open", "os.listdir", "os.scandir", "os.system", "os.exec",
                "os.posix_spawn", "os.spawn", "os.startfile", "os.fork", "os.forkpty",
            )
            or event.startswith(("subprocess.", "socket.", "ctypes.", "winreg."))
        ):
            denied.append(event)
            raise RuntimeError("depth preparation attempted external access: " + event)

    sys.addaudithook(audit)
    no_op_refused = False
    try:
        options = {"native_locator": TARGET, "written_at": EPOCH}
        original_depth = PlanPartWrite(document).DepthValue
        if requested_unit == "m":
            try:
                prepare_generation_input(document, {"dimension": "depth", "value_mm": 12.5}, **options)
            except ValueError as error:
                if str(error) != "the SOLIDWORKS depth edit must change the native driving value":
                    raise
                no_op_refused = True
            else:
                raise ValueError("exact metre-to-millimetre no-op was accepted")

        edit = {"dimension": "depth", "value_mm": EDIT_MM}
        prepared = prepare_generation_input(document, edit, **options)
        driver, = prepared.parameters
        boss, = prepared.feature_timeline
        value = driver.value
        expected_native = EDIT_MM * 0.001
        if (value.value, value.unit) != (EDIT_MM, "mm") or boss.definition.length != value:
            raise ValueError(f"absolute edit failed to bind millimetres to both {requested_unit} owners")
        if PlanPartWrite(prepared).DepthValue.hex() != expected_native.hex():
            raise ValueError("prepared edit differs from the exact authored millimetre value")
        encoded = encode_writer_input(prepared)
        replay = decode_writer_input(encoded, document.source.format_id, document.source.sha256)
        candidate = generate_prepared_candidate(replay, **options)
    finally:
        active = False
    if denied or any(name.startswith(("win32com", "pythoncom")) for name in sys.modules):
        raise ValueError("depth edit crossed the guarded offline boundary")
    if before != encode_writer_input(document) or prepared.sketches != document.sketches or prepared.bodies != document.bodies:
        raise ValueError("depth edit altered its original request or its prepared geometry owners")

    decoded = open_document(candidate, source_format="solidworks.sldprt", strict=True)
    decoded_driver, = decoded.parameters
    decoded_boss, = (feature for feature in decoded.feature_timeline if feature.id == decoded_driver.owner_id)
    body, = decoded.bodies
    native = decoded_driver.attributes.get("native_value")
    topology = body.topology
    if (
        type(native) is not float or native.hex() != expected_native.hex()
        or decoded_driver.role != "driving" or decoded_driver.name != "D1"
        or decoded_boss.parameter_ids != (decoded_driver.id,)
        or decoded_boss.definition.length != decoded_driver.value
        or body.final_feature_id != decoded_boss.id or decoded.brep is None
        or (topology.solid_count, topology.face_count, topology.edge_count, topology.vertex_count) != (1, 6, 12, 8)
        or topology.volume != 10531.1
    ):
        raise ValueError("strict SDK readback did not preserve the edited D1, boss or solid")
    return {
        "source_unit": requested_unit,
        "original_depth_m_binary64": original_depth.hex(),
        "prepared_depth_unit": value.unit,
        "edited_depth_m_binary64": native.hex(),
        "source_unchanged": True,
        "exact_no_op_refused": no_op_refused,
        "external_access_attempts": len(denied),
        "candidate_sha256": sha256(candidate).hexdigest(),
        "strict_volume_mm3": topology.volume,
    }


def check(root):
    setup(root)
    neutral = (root / "re/solidworks/measurements/2026/EncoderRoundTrip/Requests/BaselineReconstruction.json").read_bytes()
    results = []
    for unit, value in (("m", 0.0125), ("in", 0.5)):
        document = authored_request(neutral, unit, value)
        request = {"source_json": document.to_json(), "source_unit": unit}
        with TemporaryDirectory(prefix="KitDepthUnits-") as empty:
            result = subprocess.run(
                [sys.executable, "-I", "-B", str(Path(__file__).resolve()), "--root", str(root), "--worker"],
                input=json.dumps(request), cwd=empty, capture_output=True, text=True, timeout=90, check=False,
            )
        if result.returncode:
            raise ValueError(result.stderr)
        results.append(json.loads(result.stdout))
    if len({case["candidate_sha256"] for case in results}) != 1:
        raise ValueError("identical absolute edits produced different archives across source units")
    return {
        "schema": "kit.sw2026.absolute-depth-unit-replay.v1",
        "fresh_processes": len(results),
        "native_launches": 0,
        "results": results,
    }


if __name__ == "__main__":
    parser = ArgumentParser(description="Verify authored source length units at the SOLIDWORKS research edit boundary")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--worker", action="store_true")
    args = parser.parse_args()
    report = edit_and_emit(args.root.resolve(), json.load(sys.stdin)) if args.worker else check(args.root.resolve())
    print(json.dumps(report, sort_keys=True, allow_nan=False))
