from dataclasses import replace
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path, PureWindowsPath
from subprocess import run
import sys
from tempfile import TemporaryDirectory

HERE = Path(__file__).resolve()
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(ROOT / "src"))

from CheckMeasuredPartWriter import check_custody, read_pinned
from CheckScopedPlainWriter import WriterAudit

FORMAT = "solidworks.sldprt"
OPTION = "solidworks_native_measurement"
RECEIPT = "re/solidworks/measurements/2026/SdkDefaultPartNative01.json"
RECEIPT_SHA = "273b95745b147c6acaf4e51130bd521687651ad65d2edcb29f79ab50a9c3b7bc"


def require(predicate, problem):
    if not predicate:
        raise ValueError(problem)


def contrasts(document):
    body, = document.bodies
    return {
        "unknown_metadata": replace(document, metadata=dict(document.metadata, extra=True)),
        "changed_topology": replace(document, bodies=(replace(body, topology=replace(body.topology, face_count=17)),)),
        "changed_source_hash": replace(document, source=replace(document.source, sha256="0" * 64)),
        "changed_retained_bytes": replace(document, metadata=dict(document.metadata, solidworks_source_bytes=b"not the archive")),
    }


def worker(job, folder):
    from codecs import lookup
    from importlib import import_module

    native = job["locator"]
    target = folder / PureWindowsPath(native).name
    audit = WriterAudit(ROOT / "src", target)
    sys.addaudithook(audit.observe)
    from convert import open_document, write_document
    from convert.adapters.base.WriteOptions import WriteOptions
    from convert.adapters.solidworks.Core.Preparation.PrepareNative import PrepareNative
    from convert.adapters.solidworks.Core.Writing.SldprtWriter import SldprtWriter
    from interchange.document.Models.DocumentModel import CadDocument

    for codec in ("utf-8", "utf-16-le", "latin-1", "cp1252"):
        lookup(codec)
    import_module("interchange.document.Models.DocumentProvenance")
    document = CadDocument.from_json(job["document"])
    driver, = document.parameters
    require(document.brep is not None and driver.owner_id == document.bodies[0].final_feature_id
            and driver.name == "D1" and document.sketches[0].closed_profile_entity_ids
            and driver.attributes["typed_archive_owner"]["value_field"] == "f58",
            "strict input lacks its editable typed owner or cold solid")
    options = {"final_destination": native, OPTION: job["evidence"], "require_native_transfers": True}

    def transfer(model, sink, direct=False, format_id=FORMAT):
        if direct:
            return SldprtWriter().write(model, sink, WriteOptions(values=options))
        return write_document(model, sink, destination_format=format_id, allow_carrier=False, values=options)

    rejected = []
    audit.phase = "write"
    for label, variant in contrasts(document).items():
        for direct in (False, True):
            sink = BytesIO(b"unchanged")
            try:
                transfer(variant, sink, direct)
            except ValueError as error:
                require("differs from its regenerated part" in str(error), str(error))
            else:
                raise ValueError(f"{label} unexpectedly wrote a part")
            require(sink.getvalue() == b"unchanged" and sink.tell() == 0, "refusal modified a stream")
        rejected.append(label)
    other = BytesIO(b"unchanged")
    try:
        transfer(document, other, format_id="interchange.json")
    except ValueError as error:
        require("native-only feature definitions" in str(error), str(error))
    else:
        raise ValueError("another destination bypassed its native-only guard")
    require(other.getvalue() == b"unchanged" and other.tell() == 0, "other destination changed bytes")
    candidate = PrepareNative(document, BytesIO(), options[OPTION]["written_at"], WriteOptions(values=options))
    registry, direct = BytesIO(), BytesIO()
    outcomes = (transfer(document, registry), transfer(document, direct, True), transfer(document, target))
    audit.phase = "done"
    payload = candidate.BytesValue
    digest = sha256(payload).hexdigest()
    require(digest == job["output_sha256"] and candidate.BytesValue == registry.getvalue()
            == direct.getvalue() == target.read_bytes(), "internal or public bytes changed")
    require(all(outcome.vendor_loadable and outcome.application_usable and not outcome.dropped
                and outcome.native_capabilities == document.capabilities for outcome in outcomes),
            "normal routes did not attest every exactly reproduced domain")
    require(document == open_document(payload) and not audit.denied and audit.target_opens == 1,
            "strict readback or no-input-read boundary changed")
    return {"role": job["role"], "sha256": digest, "bytes": len(payload), "native_transfers": len(document.capabilities),
            "editor_depth_mm": driver.value.value, "point_count": len(document.sketches[0].entities),
            "refusals_both_routes": rejected, "other_destination_refused": True, "normal_routes": 3,
            "runtime_input_reads": len(audit.denied), "staged_file_writes": audit.target_opens}


def supervise(native, output):
    from convert import open_document

    receipt = read_pinned(ROOT / RECEIPT, RECEIPT_SHA)
    written_at = check_custody(native, receipt)
    results = []
    for row in receipt["builds"]:
        role = row["role"]
        request = read_pinned(native / role / "SdkRequest.json", row["request_sha256"])
        locator = request["expected_locator"]
        require(request["written_at"] == written_at, "measured event differs")
        raw = (native / role / PureWindowsPath(locator).name).read_bytes()
        require(sha256(raw).hexdigest() == row["candidate_sha256"], "disclosed file differs")
        job = {"role": role, "locator": locator, "output_sha256": row["candidate_sha256"],
               "evidence": {"written_at": written_at, "receipt": receipt},
               "document": open_document(raw).to_json(indent=None)}
        with TemporaryDirectory(prefix="KitColdPartWrite-") as folder:
            completed = run([sys.executable, "-I", "-B", str(HERE), "--worker", str(Path(folder).resolve())],
                            input=json.dumps(job), capture_output=True, text=True, check=False, timeout=90)
        require(completed.returncode == 0 and not completed.stderr, completed.stderr)
        results.append(json.loads(completed.stdout))
    report = {"schema": "kit.sw2026.measured-cold-part-roundtrip.v1", "cases": results,
              "method_sha256": sha256(HERE.read_bytes()).hexdigest(), "native_measurement_sha256": RECEIPT_SHA,
              "fresh_worker_processes": len(results), "native_launches": 0, "protected_inputs_read": 0}
    raw = (json.dumps(report, indent=2, sort_keys=True) + "\n").encode()
    with output.open("xb") as stream:
        stream.write(raw)
    print(sha256(raw).hexdigest())


if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument("--native", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--worker", type=Path)
    args = parser.parse_args()
    if args.worker:
        print(json.dumps(worker(json.load(sys.stdin), args.worker)))
    elif args.native is None or args.output is None:
        parser.error("--native and --output are required")
    else:
        supervise(args.native, args.output)
