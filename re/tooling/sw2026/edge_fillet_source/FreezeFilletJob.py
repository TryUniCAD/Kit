from argparse import ArgumentParser
import json
from pathlib import Path
import re
from subprocess import check_output

from FilletModel import predict, require, validate_cases
from FilletPacket import BUILD, CONTROL, ORACLE, OWNED_TOOLS, SCHEMA, SHARED_TOOLS, digest, inspect_packet, job_bytes, windows_paths

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
RESEARCH = HERE.relative_to(ROOT).as_posix()
SHARED = HERE.parent.relative_to(ROOT).as_posix()


def git(*arguments):
    return check_output(("git", "-C", str(ROOT), *arguments))


def prepare(revision, control, output, guest_packet, guest_capture, guest_checkout):
    require(re.fullmatch("[0-9a-f]{40}", revision), "expected the full committed authoring revision")
    require(git("rev-parse", revision + "^{commit}").decode().strip() == revision, "source revision does not pin a commit")
    tree = git("rev-parse", revision + "^{tree}").decode().strip()
    packet, capture, checkout = windows_paths(guest_packet, guest_capture, guest_checkout)
    require(output.is_absolute() and not output.exists() and not output.resolve().is_relative_to(ROOT),
            "host packet requires a new absolute research path outside the repository")
    require(control.is_file() and digest(control) == CONTROL, "control is not the exact healthy disclosed native part")
    data = {"Spec.json": git("show", revision + ":" + RESEARCH + "/DisclosedFilletInputs.json"),
            "Control.SLDPRT": control.read_bytes()}
    for parent, names in ((RESEARCH, OWNED_TOOLS), (SHARED, SHARED_TOOLS)):
        for name in names:
            data[f"Tool/{name}"] = git("show", revision + ":" + parent + "/" + name)
    cases = validate_cases(json.loads(data["Spec.json"]))
    output.mkdir(parents=True, exist_ok=False)
    (output / "Tool").mkdir()
    for name, contents in data.items():
        with (output / name).open("xb") as stream:
            stream.write(contents)
    manifest = {name: {"bytes": len(value), "sha256": digest(output / name)} for name, value in data.items()}
    job = {"schema": SCHEMA, "cohort": "disclosed", "source_revision": revision, "source_tree": tree,
           "oracle_sha256": ORACLE, "oracle_build": BUILD, "control_sha256": CONTROL, "files": manifest,
           "guest_packet": packet, "guest_capture": capture, "guest_checkout": checkout,
           "source_writer_implemented": False, "writer_output_count": 0}
    job_path = output / "SourceJob.json"
    with job_path.open("xb") as stream:
        stream.write(job_bytes(job))
    pin = digest(job_path)
    inspect_packet(job_path, pin)
    predictions = {case["name"]: {phase: predict(case, case[key] / 1000)
                                  for phase, key in (("initial", "radius_mm"), ("edited", "edit_radius_mm"))}
                   for case in cases}
    return {"source_job_sha256": pin, "source_revision": revision, "source_tree": tree,
            "source_spec_sha256": manifest["Spec.json"]["sha256"], "predictions_m": predictions,
            "host_native_launches": 0}


def main():
    flags = ArgumentParser(description="freeze the exact disclosed fillet source acquisition packet without starting CAD")
    flags.add_argument("--source-revision", required=True)
    flags.add_argument("--control", type=Path, required=True)
    flags.add_argument("--output", type=Path, required=True)
    flags.add_argument("--guest-packet", required=True)
    flags.add_argument("--guest-capture", required=True)
    flags.add_argument("--guest-checkout", required=True)
    args = flags.parse_args()
    result = prepare(args.source_revision, args.control, args.output, args.guest_packet,
                     args.guest_capture, args.guest_checkout)
    print(json.dumps(result, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
