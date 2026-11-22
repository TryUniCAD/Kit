from argparse import ArgumentParser
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
from subprocess import check_output, run
import sys
from tempfile import TemporaryDirectory
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE))
from SweepColdPacket import CANDIDATES, COMMON_FILES, LOCK, PREWRITER, verify
from SweepEvaluationGate import DISCLOSED_JOB, DISCLOSED_RESULT, PREWRITER_PATH, SDK_TREE, WRITER, verified_file, verify_result
from SweepEvaluationPacket import EVALUATOR, METHOD, METHOD_SCHEMA, PRODUCER, REQUIRED_NATIVE_PARITY
from SweepEvaluationPacket import extract_writer, guest_base, inventory, produce, read_method, write_files
from SweepModel import require
from SweepPacket import BUILD, FAMILY, ORACLE, digest, job_bytes


def git(*args):
    return check_output(("git", "-C", str(ROOT), *args))


def committed(revision, name):
    return git("show", f"{revision}:{name}")


def writer_archive(revision):
    require(git("rev-parse", f"{WRITER}:src").decode().strip() == SDK_TREE
            and git("rev-parse", f"{revision}:src").decode().strip() == SDK_TREE,
            "protected method source tree differs from the disclosed native 02 writer")
    for ancestor in (PREWRITER, WRITER):
        require(run(("git", "-C", str(ROOT), "merge-base", "--is-ancestor", ancestor, revision),
                    check=False).returncode == 0, "source lock and disclosed writer must precede the method")
    command = sys.executable, "-I", "-B", str(ROOT / PRODUCER), "--closure"
    closure = json.loads(check_output(command))
    require(PRODUCER in closure and len(set(closure)) == len(closure)
            and all(Path(name).suffix == ".py" and name.startswith("re/tooling/sw2026/") for name in closure),
            "producer imports an unbound research module")
    research = {name: committed(WRITER, name) for name in closure if name != PRODUCER}
    require(all((ROOT / name).read_bytes() == contents for name, contents in research.items()),
            "producer research modules differ from the corrected disclosed writer")
    archive = BytesIO(git("archive", "--format=zip", WRITER, "--", "src"))
    research[PRODUCER] = (ROOT / PRODUCER).read_bytes()
    with ZipFile(archive, "a") as writer:
        for name, contents in sorted(research.items()):
            entry = ZipInfo(name)
            entry.compress_type = ZIP_DEFLATED
            writer.writestr(entry, contents)
    return archive.getvalue(), closure


def parity(raw, closure, folder, job, spec):
    rows = []
    with TemporaryDirectory(prefix="KitSweepEvaluation") as temporary:
        writer = Path(temporary).resolve() / "Writer"
        extract_writer(raw, writer, closure)
        for relative, case in zip(CANDIDATES, spec["cases"], strict=True):
            request = {key: case[key] for key in ("name", "section_radius_m", "path_radius_m")}
            request.update(density_kg_m3=spec["density_kg_m3"], self_locator=job["candidates"][relative])
            generated, proof = produce(writer, request)
            require(generated == verified_file(folder / relative, job["files"][relative]["sha256"]),
                    "protected producer changed the native-tested disclosed bytes at the same locator")
            rows.append({"name": case["name"], **proof})
    require(tuple(row["name"] for row in rows) == REQUIRED_NATIVE_PARITY, "missing exact disclosed parity rows")
    return rows


def freeze(args):
    revision = git("rev-parse", "HEAD").decode().strip()
    folder = args.disclosed_packet.resolve()
    job, spec, _ = verify(folder / "SweepJob.json", DISCLOSED_JOB)
    require((job["writer_revision"], job["sdk_tree"]) == (WRITER, SDK_TREE), "wrong disclosed repair writer")
    if not args.parity_only:
        require(args.disclosed_pin == DISCLOSED_RESULT, "freeze on the actual passing disclosed 02 native result")
        result_raw = verified_file(args.disclosed_result.resolve(), args.disclosed_pin)
        comparison = json.loads(verified_file(folder / "DisclosedComparison.json",
                                              job["files"]["DisclosedComparison.json"]["sha256"]))
        verify_result(json.loads(result_raw), job, DISCLOSED_JOB, comparison)
        for name in (*EVALUATOR, "FreezeSweepEvaluation.py", "SweepColdPacket.py", "RunSweepCold.py", Path(PRODUCER).name):
            require((HERE / name).read_bytes() == committed(revision, f"{FAMILY}/{name}"),
                    "commit the exact method implementation before freezing")
    archive, closure = writer_archive(revision)
    rows = parity(archive, closure, folder, job, spec)
    if args.parity_only:
        return {"writer_revision": WRITER, "writer_sha256": sha256(archive).hexdigest(),
                "closure_files": len(closure), "cases": rows, "native_processes_started": 0}
    evidence = committed(PREWRITER, PREWRITER_PATH)
    require(sha256(evidence).hexdigest() == LOCK and args.output.is_absolute()
            and not args.output.resolve().is_relative_to(ROOT), "expected the original pre-writer lock and an unused external output")
    data = {name: verified_file(folder / name, job["files"][name]["sha256"])
            for name in COMMON_FILES - {"Spec.json", "Predictions.json", "Tool/RunSweepCold.py", "Tool/SweepColdPacket.py"}}
    data.update({f"Tool/{name}": committed(revision, f"{FAMILY}/{name}")
                 for name in (*EVALUATOR, "SweepColdPacket.py", "RunSweepCold.py")})
    data.update({"SourceLock.json": evidence, "Writer.zip": archive, "DisclosedResult.json": result_raw})
    method = {"schema": METHOD_SCHEMA, "files": inventory(data), "disclosed_job_sha256": DISCLOSED_JOB,
              "disclosed_result_sha256": args.disclosed_pin, "prewriter_lock_sha256": LOCK,
              "writer_revision": WRITER, "sdk_tree": SDK_TREE, "method_revision": revision, "writer_research": closure,
              "guest_root": args.guest_root, "guest_checkout": job["guest_checkout"], "oracle_build": BUILD,
              "oracle_sha256": ORACLE, "parity": [row["name"] for row in rows]}
    guest_base(method)
    write_files(args.output, data | {METHOD: job_bytes(method)})
    method_path = args.output.resolve() / METHOD
    pin = digest(method_path)
    read_method(method_path, pin)
    return {"method_sha256": pin, "writer_sha256": method["files"]["Writer.zip"]["sha256"],
            "cases": rows, "method_revision": revision, "native_processes_started": 0}


def main():
    parser = ArgumentParser(description="Freeze a data-only sweep evaluator after the disclosed native 02 pass")
    parser.add_argument("--disclosed-packet", type=Path, required=True)
    parser.add_argument("--parity-only", action="store_true")
    parser.add_argument("--disclosed-result", type=Path)
    parser.add_argument("--disclosed-pin")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--guest-root")
    args = parser.parse_args()
    options = args.disclosed_result, args.disclosed_pin, args.output, args.guest_root
    if (args.parity_only and any(options)) or (not args.parity_only and not all(options)):
        parser.error("provide the exact disclosed 02 result, digest, new output and guest root to freeze")
    print(json.dumps(freeze(args), sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
