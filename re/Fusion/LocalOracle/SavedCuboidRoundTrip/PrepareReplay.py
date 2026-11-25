import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys


def pinned_archive(path, expected):
    content = path.read_bytes()
    if path.suffix.casefold() != ".f3d" or sha256(content).hexdigest() != expected:
        raise ValueError(f"{path.name} does not match the pinned Fusion archive")
    return content


def main():
    parser = argparse.ArgumentParser(description="Prepare an exact Fusion candidate and pinned independent control for native replay.")
    parser.add_argument("case", choices=("baseline", "holdout"))
    parser.add_argument("output", type=Path)
    parser.add_argument("--role", choices=("reconstruction", "edited"), required=True)
    for role in ("source", "candidate", "control"):
        parser.add_argument(f"--{role}", type=Path, required=True)
        parser.add_argument(f"--{role}-sha256", required=True)
    args = parser.parse_args()
    pinned_archive(args.source, args.source_sha256)
    pinned_archive(args.candidate, args.candidate_sha256)
    control = pinned_archive(args.control, args.control_sha256)
    if args.control_sha256 in (args.source_sha256, args.candidate_sha256):
        raise ValueError("the control must be independently authored")
    output = args.output.resolve()
    folder = Path(__file__).resolve().parent
    regular_prepare = folder.parent / "EncoderRoundTrip" / "Prepare.py"
    subprocess.run([
        sys.executable, "-B", str(regular_prepare), args.case, str(args.candidate), str(output),
        "--source", str(args.source), "--role", args.role,
    ], check=True)
    batch = json.loads((output / "Batch.json").read_bytes())
    if (batch["source_sha256"], batch["candidate_sha256"]) != (args.source_sha256, args.candidate_sha256):
        raise ValueError("the source or candidate changed during replay preparation")
    (output / "VendorControl.f3d").write_bytes(control)
    control_helper = folder / "MeasureReplay.py"
    control_script_sha = sha256(control_helper.read_bytes()).hexdigest()
    wrapper = output / "ControlBefore" / "ControlBefore.py"
    wrapper.write_text(
        "from hashlib import sha256\n"
        "from pathlib import Path\n"
        "import runpy\n"
        f"helper = Path({str(control_helper)!r})\n"
        f"if sha256(helper.read_bytes()).hexdigest() != {control_script_sha!r}:\n"
        "    raise RuntimeError('Pinned control helper changed')\n"
        f"runpy.run_path(str(helper))['pinned_control'](Path({str(output / 'Batch.json')!r}), {args.control_sha256!r})\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
