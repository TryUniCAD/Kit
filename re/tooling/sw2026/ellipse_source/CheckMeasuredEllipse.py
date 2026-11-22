from argparse import ArgumentParser
from codecs import lookup
from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
from importlib import import_module
from io import BytesIO
from math import isclose
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
sys.path[:0] = [str(ROOT), str(ROOT / "src"), str(HERE.parent)]
from ColdEllipseModel import make_document
from EllipseMeasuredReceipt import normalize
from EllipseModel import require

FORMAT = "solidworks.sldprt"
OPTION = "solidworks_native_measurement"


def reject(action, reason):
    try:
        action()
    except ValueError as error:
        require(reason in str(error), f"unexpected refusal: {error}")
    else:
        raise ValueError("unexpected ellipse publication: " + reason)


def reject_path_model(document, locator, evidence):
    from convert import write_document
    from convert.adapters.base.WriteOptions import WriteOptions
    from convert.adapters.solidworks.Core.Writing.SldprtWriter import SldprtWriter

    with TemporaryDirectory(prefix="KitMeasuredEllipsePath-") as temp:
        folder = Path(temp)
        target = folder / (document.metadata["name"] + ".SLDPRT")
        prefix = b"existing part file"
        target.write_bytes(prefix)
        for values, reason in (
            ({}, "offline native measurement receipt"),
            ({OPTION: evidence, "final_destination": locator}, "no unique exact native measurement"),
        ):
            reject(lambda: write_document(document, target, values=values, overwrite=True, allow_carrier=True), reason)
            require(target.read_bytes() == prefix and tuple(folder.iterdir()) == (target,),
                    "unqualified host path was changed or left staging data")
        settings = WriteOptions(values={OPTION: evidence, "final_destination": locator}, overwrite=True)
        reject(lambda: SldprtWriter().write(document, target, settings), "actual final filesystem locator")
        require(target.read_bytes() == prefix and tuple(folder.iterdir()) == (target,),
                "explicit foreign path changed the direct writer target")
    return 3


def contrasts(document, request, source):
    receipt = request["evidence"]
    slot = request["slot"]
    values = {"final_destination": request["locator"], OPTION: receipt}
    negative = {
        "absent": (document, {"final_destination": request["locator"]}, "offline native measurement receipt"),
        "wrong_epoch": (document, values | {OPTION: receipt | {"written_at": request["epoch"] + 1}}, "no unique exact native measurement"),
        "changed_locator": (document, values | {"final_destination": "C:\\Unmeasured\\" + document.metadata["name"] + ".SLDPRT"},
                            "no unique exact native measurement"),
    }
    for label, tamper, message in (
        ("wrong_build", lambda report: report["oracle"].update(build="34.0.0.0"), "exact passing SOLIDWORKS"),
        ("failed_control", lambda report: report["phases"][0].update(passed=False), "failed or unowned native phase"),
        ("duplicate_lifetime", lambda report: report["phases"][1].update(lifetime=report["phases"][0]["lifetime"]), "repeats a process"),
        ("wrong_reported_locator", lambda report: report["cases"][slot].update(locator="unexpected part locator"), "generated scope or locator"),
        ("foreign_derivative", lambda report: report["cases"][slot].update(edited_sha256="b" * 64), "exact native edit and saved reopen"),
        ("wrong_measured_depth", lambda report: report["cases"][slot]["states"][0].update(depth_m=.0001), "generated driving depth"),
        ("missing_live_d1", lambda report: report["cases"][slot]["states"][1].update(readonly=True), "owned native history"),
    ):
        changed = deepcopy(receipt)
        tamper(changed["receipt"])
        negative[label] = document, values | {OPTION: changed}, message
    boss, = document.feature_timeline
    driver, = document.parameters
    depth = replace(driver.value, value=driver.value.value + 1)
    model = replace(document, parameters=(replace(driver, value=depth),),
                    feature_timeline=(replace(boss, definition=replace(boss.definition, length=depth)),))
    negative["changed_depth"] = model, values, "no unique exact native measurement"

    for model, options, message in negative.values():
        sink = BytesIO()
        reject(lambda: source(model, sink, options), message)
        require(not sink.tell() and not sink.getvalue(), "refusal wrote to a valid empty destination")
    for prefix, cursor in ((b"previous suffix", 0), (b"previous prefix", 15), (b"", 24)):
        sink = BytesIO(prefix)
        sink.seek(cursor)
        reject(lambda: source(document, sink, values), "empty seekable binary stream")
        require(sink.getvalue() == prefix and sink.tell() == cursor, "standalone refusal changed caller bytes or cursor")
    return {"receipt_or_model_refusals": list(negative), "incompatible_caller_streams": 3}


def worker(request):
    from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit
    from convert import open_document, write_document
    from convert.adapters.base.WriteOptions import WriteOptions
    from convert.adapters.solidworks.Core.Adapter import SldprtAdapter
    from convert.adapters.solidworks.Core.Preparation.Ellipse.PrepareEllipse import PrepareEllipse
    from convert.adapters.solidworks.Core.Writing.SldprtWriter import SldprtWriter

    document = make_document(request["model"])
    epoch = request["epoch"]
    locator = request["locator"]
    evidence = request["evidence"]
    path_refusals = reject_path_model(document, locator, evidence)

    for module in ("interchange.brep.Validation.BrepValidate",
                   "interchange.document.Behavior.DocumentIo", "interchange.document.Models.DocumentProvenance",
                   "interchange.document.Validation.DocumentValidate", "interchange.document.Validation.DocumentAssemblyValidate",
                   "interchange.document.Validation.DocumentFeatureValidate", "interchange.document.Validation.DocumentReferenceValidate"):
        import_module(module)
    for codec in ("ascii", "utf-8", "utf-16-le", "latin-1", "cp1252"):
        lookup(codec)
    audit = BuildAudit(HERE.parents[1] / "serial/defs")
    sys.addaudithook(audit.InspectEvent)
    audit.BeginBuild()
    internal = PrepareEllipse(document, BytesIO(), epoch, WriteOptions(values={"final_destination": locator}))
    values = {"final_destination": locator, OPTION: evidence}
    entry_points = {
        "registry": lambda doc, sink, settings: write_document(doc, sink, destination_format=FORMAT,
                                                               allow_carrier=True, validate=False, values=settings),
        "adapter": lambda doc, sink, settings: SldprtAdapter().write(doc, sink, WriteOptions(values=settings)),
        "direct": lambda doc, sink, settings: SldprtWriter().write(doc, sink, WriteOptions(values=settings)),
    }
    expected = request["expected_sha256"]
    results = {}
    for label, publish in entry_points.items():
        target = BytesIO()
        result = publish(document, target, values)
        require(target.getvalue() == internal.BytesValue and sha256(target.getvalue()).hexdigest() == expected
                and result.application_usable and result.vendor_loadable and not result.dropped
                and result.bytes_written == target.tell() == len(internal.BytesValue)
                and result.metadata[OPTION]["generated_sha256"] == expected,
                "native tested archive parity or qualified output evidence is missing")
        if label != "adapter":
            results[label] = contrasts(document, request, publish)
    recovered = open_document(internal.BytesValue, source_format=FORMAT, include_brep=False)
    sketch, = recovered.sketches
    entity, = sketch.entities
    driver, = recovered.parameters
    require(entity.kind == "ellipse" and sketch.closed_profile_entity_ids == ((entity.id,),)
            and driver.name == "D1" and driver.role == "driving"
            and driver.owner_id == recovered.bodies[0].final_feature_id
            and isclose(driver.value.value, request["model"]["depth_mm"], rel_tol=1e-14)
            and len(recovered.feature_timeline) == 19 and not recovered.validate(),
            "the measured writer route lost linked typed ellipse or D1 readback")
    require(not audit.DeniedReads and not any(name.startswith(("pythoncom", "win32com")) for name in sys.modules),
            "ellipse publication escaped the file and CAD runtime guard")
    return {"case": request["model"]["name"], "archive_sha256": expected, "streams": len(internal.StreamsValue),
            "scope": list(entry_points), "contrasts": results, "posix_path_refusals": path_refusals,
            "runtime_input_file_reads": 0, "readback_features": 19}


def write_json(path, value):
    with path.open("x") as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")
    return sha256(path.read_bytes()).hexdigest()


def supervise(native, output, receipt_output):
    receipt, requests = normalize(native)
    results = []
    for row, request in zip(receipt["cases"], requests, strict=True):
        request |= {"slot": row["slot"], "expected_sha256": row["archive_sha256"],
                    "evidence": {"written_at": request["epoch"], "receipt": receipt}}
        outcome = subprocess.run([sys.executable, "-I", "-B", str(HERE), "--worker"],
                                 input=json.dumps(request), capture_output=True, text=True, check=False, timeout=90)
        require(outcome.returncode == 0 and not outcome.stderr, outcome.stderr)
        results.append(json.loads(outcome.stdout))
    publication = ROOT / "src/convert/adapters/solidworks/Core/Writing"
    adapters = ROOT / "src/convert/adapters"
    files = [*publication.glob("Ellipse/*.py"), *publication.glob("Measured/*.py"),
             publication / "EmitNativeMut.py", publication / "SldprtWriter.py",
             adapters / "base/WholeStreamWriter.py", *sorted((adapters / "Staging").glob("*Whole*.py")),
             *(adapters / "Staging" / f"{name}.py" for name in ("StreamStaging", "SeekBinary", "SinkExtentMut"))]
    reference = write_json(receipt_output, receipt)
    print(write_json(output, {
        "schema": "kit.sw2026.measured-ellipse-publication-proof.v1",
        "guarded_processes": len(results), "results": results,
        "disclosed_native_result_sha256": receipt["native_result_sha256"], "native_launches": 0, "heldout_credit": 0,
        "normalized_receipt_sha256": reference, "native_processes": receipt["fresh_processes"],
        "native_checks": sum(phase["checks"] for phase in receipt["phases"]),
        "src_sha256": {path.relative_to(ROOT).as_posix(): sha256(path.read_bytes()).hexdigest() for path in sorted(files)},
        "method": {path.name: sha256(path.read_bytes()).hexdigest() for path in (HERE, HERE.with_name("EllipseMeasuredReceipt.py"))},
    }))


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--native", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()
    if args.worker:
        print(json.dumps(worker(json.load(sys.stdin)), sort_keys=True))
    else:
        supervise(args.native, args.output, args.receipt)
