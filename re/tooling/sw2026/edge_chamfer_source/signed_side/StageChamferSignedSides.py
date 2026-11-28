from argparse import ArgumentParser
from pathlib import Path, PureWindowsPath
from subprocess import check_output
import json
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[5]
sys.path[:0] = [str(HERE.parent.parent), str(HERE.parent.parent.parent / "edge_fillet_source")]

from ChamferModel import predictions, validate_spec
from ChamferPacket import TOOLS, SCHEMA, create_packet
from FilletModel import require
from FilletPacket import BUILD, CONTROL, ORACLE, digest, job_bytes, windows_paths

PUBLIC = "ChamferSignedSideSource01"
GUEST = PureWindowsPath(r"C:\KitChamferSignedSideSource01")
CHECKOUT = r"\\Mac\Home\Documents\UniCAD\Kit"
SPEC = HERE.with_name("ChamferSignedSideInputs.json").relative_to(ROOT).as_posix()


def stage(control, output):
    require(output.is_absolute() and output.name == "Packet" and output.parent.name == PUBLIC
            and not output.exists() and not output.resolve().is_relative_to(ROOT),
            "use the unused managed signed-side source packet")
    require(digest(control) == CONTROL, "native source control seal differs")

    def git(*args):
        return check_output(("git", "-C", str(ROOT), *args))

    revision = git("rev-parse", "HEAD").decode().strip()
    require(not git("status", "--porcelain", "--", HERE.parent.relative_to(ROOT).as_posix()),
            "signed-side source inputs and method must be committed")
    packet, capture, checkout = windows_paths(str(GUEST / "Packet"), str(GUEST / "Capture"), CHECKOUT)
    data = {f"Tool/{name}": git("show", f"{revision}:{path}/{name}") for path, names in TOOLS.items() for name in names}
    spec = git("show", f"{revision}:{SPEC}")
    cases = validate_spec(json.loads(spec))
    data.update({"Spec.json": spec, "Control.SLDPRT": control.read_bytes(),
                 "Predictions.json": job_bytes(predictions(cases))})
    job = {"schema": SCHEMA, "cohort": "disclosed", "source_revision": revision,
           "source_tree": git("rev-parse", f"{revision}^{{tree}}").decode().strip(),
           "oracle_build": BUILD, "oracle_sha256": ORACLE, "control_sha256": CONTROL, "writer_output_count": 0,
           "guest_packet": packet, "guest_capture": capture, "guest_checkout": checkout}
    pin = create_packet(output, job, data)
    return {"job_sha256": pin, "cases": [row["name"] for row in cases],
            "spec_sha256": job["files"]["Spec.json"]["sha256"],
            "prediction_sha256": job["files"]["Predictions.json"]["sha256"], "native_processes": 0}


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--control", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(stage(args.control, args.output), sort_keys=True))
