from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import re
from shutil import copyfile
import subprocess

from StageLocalPartProbe import CONTROL, IMPORT, ORACLE, json_data, pinned_tree, require


SOURCE_RECEIPT = "1a5a4993881c967682496c90924c262c7954fddd67dd9d1ee3e105186deed281"
OPERATORS = (
    "BuildImportedLocalPart.py", "EvaluateSealedImportedGeometry.py", "ProjectDisclosedImport.py",
    "ObserveLocalImportedPart.py", "BuildLocalBodyKernel.py", "LocalBodyKernel.py",
)
SCENE_OPERATORS = ("ProbeImportedPartScene.py", "VerifyBareImportPackage.py", "ProjectImportedSemantics.py")


def digest(data):
    return sha256(data).hexdigest()


def stage(args):
    repo = Path(__file__).resolve().parents[4]
    output = args.destination.resolve()
    require(not output.exists() and not output.is_relative_to(repo) and re.fullmatch(r"[0-9a-f]{40}", args.revision),
            "choose an unused external packet path and a full committed revision")
    public_receipt = args.sealed_source_receipt.read_bytes()
    require(digest(public_receipt) == SOURCE_RECEIPT, "the published sealed source receipt has changed")
    lock = json.loads(public_receipt)
    require(lock["passed"] and lock["controls_healthy"] and lock["heldout_sources_locked"] == 2
            and lock["heldout_payloads_shared"] == 0, "expected only the opaque source-lock receipt")
    subprocess.run(["git", "merge-base", "--is-ancestor", lock["source_revision"], args.revision], cwd=repo, check=True)
    frozen_at = int(subprocess.check_output(["git", "show", "-s", "--format=%ct", args.revision], cwd=repo))
    require(frozen_at > lock["source_batch_locked_at_unix_s"], "the original source hashes must be locked before the evaluator")
    require(digest(args.control.read_bytes()) == CONTROL, "the pristine native control has changed")
    output.mkdir()
    code = output / "Code"
    code.mkdir()
    pinned_tree(repo, args.revision, code)
    has_scene = args.scene_and_text or args.empty_file_owner or args.annotation_managers
    operator_names = OPERATORS + (SCENE_OPERATORS if has_scene else ())
    hashes = {name: digest((code / IMPORT / name).read_bytes()) for name in operator_names}
    (output / "SealedSourceReceipt.json").write_bytes(public_receipt)
    copyfile(args.control, output / "Control.SLDPRT")
    require(digest((output / "Control.SLDPRT").read_bytes()) == CONTROL, "copied control changed")
    schema, guest = ("kit.sw2026.sealed-import-geometry-job.v1", r"C:\KitImportedEvaluation01")
    if args.scene_and_text:
        schema, guest = ("kit.sw2026.sealed-import-scene-text-job.v1", r"C:\KitImportedEvaluation02")
    if args.empty_file_owner:
        schema, guest = ("kit.sw2026.sealed-import-property-owner-job.v1", r"C:\KitImportedEvaluation03")
    if args.annotation_managers:
        schema, guest = ("kit.sw2026.sealed-import-annotation-managers-job.v1", r"C:\KitImportedEvaluation04")
    job = json_data({"schema": schema, "writer_revision": args.revision, "oracle_sha256": ORACLE,
                     "guest_output": guest, "operators": hashes})
    (output / "Job.json").write_bytes(job)
    print(json.dumps({"job_sha256": digest(job), "writer_revision": args.revision,
                      "source_receipt_sha256": SOURCE_RECEIPT}))


if __name__ == "__main__":
    parser = ArgumentParser(description="Freeze the decoder and writer after the opaque native source lock")
    parser.add_argument("destination", type=Path)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--sealed-source-receipt", type=Path, required=True)
    parser.add_argument("--control", type=Path, required=True)
    profile = parser.add_mutually_exclusive_group()
    profile.add_argument("--scene-and-text", action="store_true")
    profile.add_argument("--empty-file-owner", action="store_true")
    profile.add_argument("--annotation-managers", action="store_true")
    stage(parser.parse_args())
