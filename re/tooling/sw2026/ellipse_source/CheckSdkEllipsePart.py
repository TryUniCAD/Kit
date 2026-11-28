from base64 import b64decode, b64encode
from codecs import lookup
from dataclasses import replace
from hashlib import sha256
from importlib import import_module
from io import BytesIO
from pathlib import Path, PureWindowsPath
import json
import subprocess
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
sys.path[:0] = [str(ROOT), str(ROOT / "src"), str(HERE.parent)]


def digest(data):
    return sha256(data).hexdigest()


def worker():
    from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit

    audit = BuildAudit(HERE.parents[1] / "serial" / "defs")
    sys.addaudithook(audit.InspectEvent)
    from convert import write_document
    from convert.adapters.base.WriteOptions import WriteOptions
    from convert.adapters.solidworks.Core.Adapter import SldprtAdapter
    from convert.adapters.solidworks.Core.Preparation.Ellipse.PrepareEllipse import PrepareEllipse
    from interchange.document.Behavior.DocumentIo import FromJson
    from interchange.document.Models.DocumentModel import CadDocument
    from interchange.document.Validation.DocumentAssemblyValidate import GetAssemblyErrs
    from interchange.document.Validation.DocumentFeatureValidate import GetFeatureErrs
    from interchange.document.Validation.DocumentReferenceValidate import GetRefErrors

    request = json.loads(sys.stdin.buffer.read())
    if set(request) != {"document", "locator", "epoch"}:
        raise ValueError("ellipse worker requires a neutral document and ordinary final output")
    document = FromJson(CadDocument, request["document"])
    shape, = document.sketches
    entity, = shape.entities
    parameter, = document.parameters
    feature, = document.feature_timeline
    ellipse = entity.geometry
    blocked = []
    import_module("interchange.document.Models.DocumentProvenance")
    import_module("convert.adapters.solidworks.Core.Writing.EmitNativeMut").ReadTime = lambda: request["epoch"]

    def guard(event, _args):
        if event.startswith(("socket.", "ctypes.", "winreg.")) or event in ("os.startfile", "os.startfile/2"):
            blocked.append(event)
            raise PermissionError("ellipse preparation attempted an external process or service")

    for encoding in ("ascii", "utf-8", "utf-16-le", "latin-1", "cp1252"):
        lookup(encoding)
    sys.addaudithook(guard)
    audit.BeginBuild()
    options = WriteOptions(values={"final_destination": request["locator"], "require_native_transfers": True})
    target = BytesIO()
    outcome = PrepareEllipse(document, target, request["epoch"], options)
    if target.tell() or target.getvalue():
        raise ValueError("preparation unexpectedly opened its caller-owned destination")
    config, = document.configurations
    adapter_result = SldprtAdapter().write(document, target, replace(options, configuration=config.name))
    sdk_target = BytesIO()
    sdk_result = write_document(document, sdk_target, destination_format="solidworks.sldprt",
                                configuration=config.id, values=options.values)
    if (target.getvalue() != outcome.BytesValue or sdk_target.getvalue() != outcome.BytesValue
            or adapter_result.bytes_written != len(outcome.BytesValue)
            or sdk_result.bytes_written != len(outcome.BytesValue)
            or sdk_result.dropped or sdk_result.carrier_capabilities):
        raise ValueError("public ellipse writer routes do not reproduce the typed constructor")
    circle = replace(shape, entities=(replace(entity, geometry=replace(ellipse, minor_radius=ellipse.major_radius)),))
    construction = replace(shape, entities=(replace(entity, construction=True),))
    reversed_boss = replace(feature, definition=replace(feature.definition, reversed=True))
    wrong_driver = replace(parameter, owner_id=shape.id)
    unknown = {**document.metadata, "unmodeled_author_intent": True}
    refused = {
        "equal_radii": (replace(document, sketches=(circle,)), options, "measured signed geometry and depth"),
        "construction": (replace(document, sketches=(construction,)), options, "free full closed entity"),
        "reversed_boss": (replace(document, feature_timeline=(reversed_boss,)), options, "single blind direction"),
        "wrong_driver": (replace(document, parameters=(wrong_driver,)), options, "driving D1 parameter"),
        "unsupported_metadata": (replace(document, metadata=unknown), options, "unprojected document metadata"),
        "requested_configuration": (document, replace(options, configuration="Missing"), "configuration is unavailable"),
        "unnamed_stream": (document, WriteOptions(), "unnamed native streams require an explicit final destination"),
    }
    refusals = {}
    for name, (challenge, settings, reason) in refused.items():
        dst = BytesIO(b"caller-defined destination")
        dst.seek(4)
        try:
            PrepareEllipse(challenge, dst, request["epoch"], settings)
        except ValueError as error:
            if reason not in str(error) or dst.tell() != 4 or dst.getvalue() != b"caller-defined destination":
                raise ValueError("unexpected scoped refusal for " + name) from error
            refusals[name] = str(error)
        else:
            raise ValueError("unqualified ellipse preparation succeeded for " + name)
    loaded = [
        name for name, module in sys.modules.items()
        if name != "__main__" and getattr(module, "__file__", None)
        and Path(module.__file__).is_relative_to(ROOT / "re")
    ]
    if audit.DeniedReads or blocked or loaded:
        raise ValueError("ellipse preparation escaped the standalone SDK boundary")
    print(json.dumps({
        "archive": b64encode(outcome.BytesValue).decode("ascii"),
        "archive_sha256": digest(outcome.BytesValue),
        "streams": {name: {"bytes": len(data), "sha256": digest(data)} for name, data in outcome.StreamsValue.items()},
        "map_frontiers": [outcome.ConfigValue.MapValue.CounterValue, outcome.ResolvedValue.MapValue.CounterValue],
        "resolved_map_base": outcome.ResolvedValue.MapBase,
        "runtime_file_reads": 0,
        "sdk_research_imports": len(loaded),
        "public_routes": ["convert.write_document", "SldprtAdapter.write"],
        "refusals": refusals,
    }, sort_keys=True, allow_nan=False))


def measure():
    from ColdEllipseModel import make_document
    from EllipseModel import CASES, predict
    from convert.adapters.solidworks.Archive.Construction.Ellipse.ProjectEllipse import ProjectEllipse
    from convert.adapters.solidworks.Container.Container import SldprtArchive
    from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink

    records = ROOT / "re/solidworks/measurements/2026"
    method = digest(HERE.read_bytes())
    construction_raw = (records / "EllipseColdPrototype02.json").read_bytes()
    oracle_raw = (records / "EllipseColdNativeDisclosed02.json").read_bytes()
    construction, oracle = map(json.loads, (construction_raw, oracle_raw))
    if not (oracle["passed"] and oracle["healthy_controls"] and oracle["fresh_processes"] == 8
            and oracle["trial_sha256"] == construction["shallow_cli_verifications"][-1]["trial_sha256"]):
        raise ValueError("disclosed byte references must come from the passing native packet")
    candidates = []
    for index, (case, reference) in enumerate(zip(CASES, construction["candidates"], strict=True)):
        axes = predict(case)["unit_axes"]
        input_value = {name: case[name] for name in ("name", "center_mm", "radii_mm", "depth_mm")}
        document = make_document(input_value | {"major_xy": axes[0][:2]})
        locator = str(PureWindowsPath(r"C:\KitEllipseColdPrototype02\Packet\Candidates") / (case["name"] + ".SLDPRT"))
        wire = json.dumps({"document": document.to_json(), "locator": locator, "epoch": 1795516920 + 61 * index}).encode()
        outcomes = [
            subprocess.run([sys.executable, "-I", "-B", str(HERE), "--worker"], input=wire,
                           capture_output=True, timeout=90, check=False)
            for _ in range(2)
        ]
        if any(run.returncode or run.stderr for run in outcomes):
            raise ValueError(next(run.stderr.decode() for run in outcomes if run.returncode or run.stderr))
        if outcomes[0].stdout != outcomes[1].stdout:
            raise ValueError("independent ellipse workers emitted different results")
        report = json.loads(outcomes[0].stdout)
        archive = b64decode(report.pop("archive"), validate=True)
        if (case["name"] != reference["case"] or len(archive) != reference["size"]
                or digest(archive) != reference["sha"] or report["archive_sha256"] != reference["sha"]):
            raise ValueError("candidate does not reproduce the native-tested archive for " + case["name"])
        candidates.append((case["name"], document, wire, report, archive))
    from CompileColdEllipse import inspect

    results = []
    for label, document, wire, report, archive in candidates:
        parsed = SldprtArchive.from_bytes(archive)
        link = ReadNativeLink(parsed, 0, ReadEllipses=True)
        neutral = ProjectEllipse(document)
        linked = inspect(neutral, archive, parsed.streams, link.ConfigValue, link.ResolvedValue)
        if (report["map_frontiers"] != [link.ConfigValue.MapValue.CounterValue, link.ResolvedValue.MapValue.CounterValue]
                or report["resolved_map_base"] != link.ResolvedValue.MapBase
                or report["streams"] != {name: {"bytes": len(data), "sha256": digest(data)} for name, data in parsed.streams.items()}):
            raise ValueError("independent readback changed a generated stream or map frontier")
        results.append(report | {"case": label, "neutral_request_sha256": digest(wire),
                                 "bytes": len(archive), "linked_replays": linked["linked_replays"],
                                 "depth_m": linked["depth_m"], "major_station_m": linked["major_station"],
                                 "linked_roots": linked["root_count"]})
    return {"schema": "kit.sw2026.sdk-full-ellipse-public.v1", "native_reference_receipt": digest(oracle_raw),
            "construction_reference_receipt": digest(construction_raw), "guarded_processes": 4,
            "method_sha256": method, "native_processes_started": 0, "cases": results}


if __name__ == "__main__":
    if sys.argv[1:] == ["--worker"]:
        worker()
    elif not sys.argv[1:]:
        print(json.dumps(measure(), indent=2, sort_keys=True, allow_nan=False))
    else:
        raise ValueError("unknown ellipse verification mode")
