from argparse import ArgumentParser
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys


def canonical(value):
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def worker(args):
    root = args.root.resolve()
    sys.path[:0] = [
        str(root / "src"),
        str(root / "re/automation"),
        str(root / "re/solidworks/WriterResearch"),
    ]
    import ComposeTopAnnotation as composition
    from convert import open_document
    from interchange.document.Models.DocumentProvenance import HasProvenance
    import interchange.document.Validation.DocumentAssemblyValidate
    import interchange.document.Validation.DocumentFeatureValidate
    import interchange.document.Validation.DocumentReferenceValidate
    import interchange.brep.Validation.BrepValidate
    from interchange.Records.RecordProvenance import Provenance
    from interchange.serialization.EncodeData import ToData

    "*Top".encode("utf-16-le").decode("utf-16-le")
    composition_hash = sha256(Path(composition.__file__).read_bytes()).hexdigest()
    grammar = root / "src/convert/adapters/solidworks/Config/RootLayout.json"
    grammar_sha256 = sha256(grammar.read_bytes()).hexdigest()
    source_methods = {}
    for module in tuple(sys.modules.values()):
        filename = getattr(module, "__file__", None)
        if filename is not None and Path(filename).resolve().is_relative_to(root):
            path = Path(filename).resolve()
            source_methods[path.relative_to(root).as_posix()] = sha256(
                path.read_bytes()
            ).hexdigest()
    require(
        not any(
            name.startswith(("win32com", "pythoncom", "comtypes"))
            for name in sys.modules
        ),
        "native CAD modules are loaded",
    )
    phase = ["calibration"]
    input_path = str(args.request.resolve())
    reads, grammar_reads, external = [], [], []

    def audit(event, values):
        if event == "open":
            if (
                phase[0] == "typed_readback"
                and str(values[0]) == str(grammar)
                and values[1] in ("r", "rb")
                and not values[2]
                & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND)
            ):
                grammar_reads.append(
                    "src/convert/adapters/solidworks/Config/RootLayout.json"
                )
                return
            if (
                phase[0] == "request"
                and str(values[0]) == input_path
                and values[1] in ("r", "rb")
                and not values[2]
                & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND)
            ):
                reads.append("named_json_request")
                return
        if event in (
            "open",
            "import",
            "os.listdir",
            "os.scandir",
            "os.system",
            "os.startfile",
            "os.exec",
            "os.posix_spawn",
        ) or event.startswith(("subprocess.", "socket.", "ctypes.")):
            external.append({"phase": phase[0], "event": event})
            raise PermissionError("Top composition forbids external access: " + event)

    sys.addaudithook(audit)
    try:
        open("top-composition-no-source", "rb")
    except PermissionError:
        require(
            external == [{"phase": "calibration", "event": "open"}],
            "file guard calibration",
        )
    else:
        raise ValueError("file guard did not refuse calibration")
    external.clear()
    phase[0] = "request"
    payload = args.request.resolve().read_bytes()
    phase[0] = "parse"
    wire = json.loads(payload)
    document, intent = composition.read_request(payload)
    original_document = canonical(document.to_dict())
    original_intent = canonical(ToData(intent.transform))
    phase[0] = "emit"
    candidate = composition.construct(
        document, intent, args.native_locator, args.written_at
    )
    require(
        canonical(document.to_dict()) == original_document
        and canonical(ToData(intent.transform)) == original_intent,
        "construction mutated source intent",
    )
    phase[0] = "typed_readback"
    structure = composition.inspect_candidate(candidate, intent)
    require(
        structure["matrix_binary64"]
        == [
            "0x1.0000000000000p+0",
            "0x0.0p+0",
            "0x0.0p+0",
            "0x0.0p+0",
            "0x0.0p+0",
            "0x1.0000000000000p+0",
            "-0x0.0p+0",
            "-0x1.0000000000000p+0",
            "-0x0.0p+0",
        ],
        "emitted Top orientation or signed-zero convention differs",
    )
    readback = open_document(
        candidate.BytesValue, source_format="solidworks.sldprt", strict=True
    )
    require(
        readback.source.sha256 == sha256(candidate.BytesValue).hexdigest(),
        "full SDK readback does not bind generated archive",
    )
    readback.assert_valid()
    require(
        not HasProvenance(document),
        "owned-neutral request contains native record provenance",
    )
    require(
        len(readback.bodies) == 1 and readback.bodies[0].topology.solid_count == 1,
        "generated full archive must read as one solid",
    )

    phase[0] = "custody_independence"
    custody = deepcopy(wire)
    custody["document"]["source"].update(
        {
            "path": "Q:/AbsentSource/NotAnInput.SLDPRT",
            "sha256": "a" * 64,
            "application_version": "custody-only",
        }
    )
    other_document, other_intent = composition.read_request(canonical(custody))
    other = composition.construct(
        other_document, other_intent, args.native_locator, args.written_at
    )
    require(
        other.BytesValue == candidate.BytesValue
        and other.StreamsValue == candidate.StreamsValue,
        "custody identity was reused in generated native streams",
    )
    refusals = []

    def reject(name, change):
        invalid = deepcopy(wire)
        change(invalid)
        before = canonical(invalid)
        phase[0] = "refusal:" + name
        parsed = None
        typed_before = None
        try:
            parsed, view = composition.read_request(before)
            typed_before = canonical(parsed.to_dict())
            composition.construct(parsed, view, args.native_locator, args.written_at)
        except (ValueError, TypeError, KeyError) as error:
            refusal = {
                "case": name,
                "exception": type(error).__name__,
                "message": str(error),
            }
        else:
            raise ValueError("unsupported intent was accepted: " + name)
        require(
            parsed is None or canonical(parsed.to_dict()) == typed_before,
            "refusal mutated typed input: " + name,
        )
        require(canonical(invalid) == before, "refusal mutated JSON request: " + name)
        refusals.append(refusal)

    reject("extra_root", lambda value: value.update({"foreign": "must not disappear"}))
    reject(
        "nonnull_aliases",
        lambda value: value["annotation_view"].update({"aliases": [7]}),
    )
    for name, field, value in (
        ("wrong_configuration", "configuration_id", "foreign-configuration"),
        ("unknown_view", "role", "custom"),
        ("perspective", "projection", "perspective"),
        ("inverse_frame", "frame_direction", "model_to_view"),
        ("metre_origin", "origin_unit", "m"),
    ):
        reject(
            name,
            lambda request, field=field, value=value: request[
                "annotation_view"
            ].__setitem__(field, value),
        )
    for name, vector, coordinate, value in (
        ("translated_origin", "origin", "x", 0.001),
        ("opposite_normal", "z_axis", "y", 1.0),
        ("wrong_up", "y_axis", "z", -1.0),
        ("scaled_axis", "x_axis", "x", 2.0),
        ("bool_component", "x_axis", "x", True),
    ):
        reject(
            name,
            lambda request, vector=vector, coordinate=coordinate, value=value: request[
                "annotation_view"
            ]["transform"][vector].__setitem__(coordinate, value),
        )
    reject(
        "foreign_document_metadata",
        lambda value: value["document"]["metadata"].update(
            {"foreign": "retain-or-refuse"}
        ),
    )
    reject(
        "retained_native_archive",
        lambda value: value["document"]["metadata"].update(
            {"solidworks_source_bytes": {"$bytes": "AQI="}}
        ),
    )
    reject(
        "foreign_transform_field",
        lambda value: value["annotation_view"]["transform"].update({"foreign": 1}),
    )
    reject(
        "source_attributes",
        lambda value: value["document"]["source"]["attributes"].update(
            {"foreign": "retain-or-refuse"}
        ),
    )
    reject(
        "configuration_attributes",
        lambda value: value["document"]["configurations"]["$tuple"][0][
            "attributes"
        ].update({"foreign": True}),
    )
    provenance = ToData(Provenance("boundary-audit", "native-record"))
    reject(
        "feature_provenance",
        lambda value: value["document"]["feature_timeline"]["$tuple"][0].__setitem__(
            "provenance", provenance
        ),
    )
    require(
        reads == ["named_json_request"] and not external,
        "composition used an unapproved external input",
    )
    return {
        "schema": "kit.sw2026.top-composition-boundary.v1",
        "request_sha256": sha256(payload).hexdigest(),
        "request_bytes": len(payload),
        "composition_sha256": composition_hash,
        "loaded_project_methods": {
            "count": len(source_methods),
            "sha256": sha256(canonical(source_methods)).hexdigest(),
        },
        "named_input_reads": reads,
        "readback_grammar": {"sha256": grammar_sha256, "reads": grammar_reads},
        "emission_external_events": external,
        "archive": {
            "bytes": len(candidate.BytesValue),
            "sha256": sha256(candidate.BytesValue).hexdigest(),
        },
        "streams": {
            name: {"bytes": len(data), "sha256": sha256(data).hexdigest()}
            for name, data in sorted(candidate.StreamsValue.items())
        },
        "typed_readback": structure,
        "source_intent_unchanged": True,
        "custody_identity_not_reused": True,
        "body": {
            "solid_count": readback.bodies[0].topology.solid_count,
            "face_count": readback.bodies[0].topology.face_count,
            "edge_count": readback.bodies[0].topology.edge_count,
            "vertex_count": readback.bodies[0].topology.vertex_count,
            "volume": readback.bodies[0].topology.volume,
        },
        "refusals": refusals,
        "models_used": False,
        "vendor_loadable": False,
        "application_usable": False,
    }


if __name__ == "__main__":
    parser = ArgumentParser(
        description="Audit full Top annotation composition from one named JSON input in a fresh process"
    )
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--native-locator", required=True)
    parser.add_argument("--written-at", type=int, required=True)
    parser.add_argument("--worker", action="store_true")
    args = parser.parse_args()
    if args.worker:
        result = worker(args)
    else:
        child = subprocess.run(
            [
                sys.executable,
                "-I",
                "-B",
                str(Path(__file__).resolve()),
                *sys.argv[1:],
                "--worker",
            ],
            capture_output=True,
            timeout=90,
            check=False,
        )
        if child.returncode:
            sys.stderr.buffer.write(child.stderr)
            raise SystemExit(child.returncode)
        result = json.loads(child.stdout)
        result["checkout_revision"] = subprocess.run(
            ["git", "-C", str(args.root.resolve()), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        ).stdout.strip()
        result["process"] = {
            "fresh_child": True,
            "returncode": child.returncode,
            "python_version": sys.version.split()[0],
        }
        result["method_sha256"] = sha256(Path(__file__).read_bytes()).hexdigest()
    sys.stdout.buffer.write(canonical(result) + b"\n")
