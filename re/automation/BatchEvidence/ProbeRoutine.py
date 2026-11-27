from argparse import ArgumentParser
from json import dumps, loads
from pathlib import Path
from sys import path, executable
from time import monotonic

path.insert(0, str(Path(__file__).resolve().parents[1]))

from CaptureTools.Catalogue.SolidWorks.RunSolidBatch import RunSolidBatch
from CaptureTools.Catalogue.SolidWorks.RunSolidPhase import RunSolidPhase
from InferenceGrid.Authoring.SolidRoutine import OwnSolidRoutine
from Records import read_record


def Equivalent(left, right):
    from math import isclose

    if isinstance(left, dict) and isinstance(right, dict):
        return left.keys() == right.keys() and all(Equivalent(left[key], right[key]) for key in left if key != "label")
    if isinstance(left, list) and isinstance(right, list):
        return len(left) == len(right) and all(Equivalent(a, b) for a, b in zip(left, right, strict=True))
    if isinstance(left, (float, int)) and isinstance(right, (float, int)):
        return isclose(left, right, rel_tol=1e-9, abs_tol=1e-6)
    return left == right


def Main():
    parser = ArgumentParser()
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--host", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    import subprocess

    revision = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
    output = args.output.resolve()
    output.mkdir()
    host = {**read_record(args.host), "verification_mode": "document_reopen", "routine_queue": str(output / "SolidWorksQueue")}
    hostfile = output / "SolidWorksHost.json"
    hostfile.write_text(dumps(host), encoding="utf-8")
    cases = loads(args.cases.read_bytes())
    started = monotonic()
    reports = []
    decodestart = decodeend = None
    overlap = False
    decodecode = ('from pathlib import Path; import sys,json,time; from convert import open_document; '
                  'start=time.monotonic(); d=open_document(Path(sys.argv[1]).read_bytes(),source_format="solidworks.sldprt",strict=False); '
                  'print(json.dumps({"started":start,"ended":time.monotonic(),"json_bytes":len(d.to_json(indent=None))}))')
    with OwnSolidRoutine(output, root, hostfile, revision):
        for index in range(2):
            destination = output / "NativeAttempts" / str(index) / "Capture"
            destination.parent.mkdir(parents=True)
            if index == 1:
                decodeoutput = (output / "Decoder.json").open("wb")
                decodeerror = (output / "Decoder.stderr").open("wb")
                decoder = subprocess.Popen([executable, "-B", "-c", decodecode, reports[0]["archives"][0]["path"]], stdout=decodeoutput, stderr=decodeerror)
                decodestart = monotonic()
            reports.extend(RunSolidBatch(cases, destination, host, Revision=revision))
            if index == 1:
                decodeend = monotonic()
                try:
                    if decoder.wait(timeout=60) != 0:
                        raise ValueError("public decoder failed during native capture")
                finally:
                    decodeoutput.close()
                    decodeerror.close()
                decoded = read_record(output / "Decoder.json")
                overlap = decoded["started"] < decodeend and decoded["ended"] > decodestart and decoded["json_bytes"] > 0
    pids = {report["measurements"]["authoring_process_id"] for report in reports}
    if len(pids) != 1 or any(report["verification_mode"] != "document_reopen" for report in reports):
        raise ValueError("routine batches did not share one owned process")
    import shutil

    fresh = output / "Fresh"
    fresh.mkdir()
    manifest = {"schema": 1, "cases": []}
    for report in reports[:len(cases)]:
        source = Path(report["archives"][0]["path"]).parent
        caseout = fresh / source.parent.name
        (caseout / source.name).mkdir(parents=True)
        for filename in ("first.json", report["receipt"]["native_files"][0]["file"]):
            shutil.copyfile(source / filename, caseout / source.name / filename)
        shutil.copyfile(source.parent / "ConfiguredCase.json", caseout / "ConfiguredCase.json")
        manifest["cases"].append({"configuration": str(caseout / "ConfiguredCase.json"), "output": str(caseout)})
    manifestfile = fresh / "BatchManifest.json"
    manifestfile.write_text(dumps(manifest), encoding="utf-8")
    RunSolidPhase(manifestfile, fresh, read_record(args.host), "second", IsBatch=True)
    comparisons = []
    for report, entry in zip(reports[:len(cases)], manifest["cases"], strict=True):
        recipe = report["case"]["recipe"]
        reopened = read_record(Path(entry["output"]) / recipe / "measurements.json")
        equal = Equivalent(report["measurements"]["observations"]["document_reopen"]["measurements"], reopened["observations"]["fresh_reopen"]["measurements"])
        comparisons.append({"recipe": recipe, "measurements_equal": equal, "fresh_pid": reopened["reopen_process_id"]})
    result = {"revision": revision, "status": "observed", "cases": len(reports), "pid": list(pids), "seconds": monotonic() - started, "decoder_overlap": overlap, "fresh_comparisons": comparisons, "native_acceptance": False}
    (output / "Probe.json").write_text(dumps(result), encoding="utf-8")
    if not overlap or not all(item["measurements_equal"] and item["fresh_pid"] not in pids for item in comparisons):
        raise ValueError("routine and fresh comparison or decoder overlap failed")
    print(output / "Probe.json")


if __name__ == "__main__":
    Main()
