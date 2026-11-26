import argparse
from hashlib import sha256
import json
from pathlib import Path


CASES = {
    "baseline": (16.4, 27.1, 13.8, 22.6, 28.3),
    "holdout": (43.7, 12.9, 24.6, 31.4, 19.7),
}
STAGES = ("ControlBefore", "Candidate", "Reopen", "ControlAfter")


def main():
    parser = argparse.ArgumentParser(description="Prepare an isolated Fusion cuboid oracle batch.")
    parser.add_argument("case", choices=CASES)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--role", choices=("reconstruction", "edited"), default="edited")
    args = parser.parse_args()
    candidate = args.candidate.resolve()
    output = args.output.resolve()
    source = args.source.resolve()
    if source.suffix.lower() != ".f3d" or candidate.suffix.lower() != ".f3d":
        parser.error("source and candidate must be Fusion .f3d archives")
    candidate_digest = sha256(candidate.read_bytes()).hexdigest()
    width, depth, original_height, edited_height, native_edit = CASES[args.case]
    encoded_height = original_height if args.role == "reconstruction" else edited_height
    script = Path(__file__).with_name("Measure.py").resolve()
    script_digest = sha256(script.read_bytes()).hexdigest()
    config = output / "Batch.json"
    output.mkdir()
    config.write_text(json.dumps({
        "case": args.case,
        "role": args.role,
        "source_sha256": sha256(source.read_bytes()).hexdigest(),
        "candidate": str(candidate),
        "candidate_sha256": candidate_digest,
        "measurement_script_sha256": script_digest,
        "width_mm": width,
        "depth_mm": depth,
        "source_height_mm": original_height,
        "encoded_height_mm": encoded_height,
        "native_edit_mm": native_edit,
    }, indent=2) + "\n", encoding="utf-8")
    for stage in STAGES:
        folder = output / stage
        folder.mkdir()
        body = (
            "from hashlib import sha256\n"
            "from pathlib import Path\n"
            "import runpy\n\n"
            "def run(context):\n"
            f"    script = Path({str(script)!r})\n"
            f"    if sha256(script.read_bytes()).hexdigest() != {script_digest!r}:\n"
            "        raise RuntimeError('Measurement script changed after batch preparation')\n"
            "    oracle = runpy.run_path(str(script))\n"
            f"    oracle['measure'](Path({str(config)!r}), {stage!r})\n\n"
            "if __name__ == '__kit_fusion_oracle__':\n"
            "    run(None)\n"
        )
        (folder / f"{stage}.py").write_text(body, encoding="utf-8")
        (folder / f"{stage}.manifest").write_text(json.dumps({
            "autodeskProduct": "Fusion",
            "type": "script",
            "id": f"KitEncoderRoundTrip{stage}",
            "author": "Kit",
            "description": {"": f"Kit Fusion cuboid oracle stage {stage}"},
            "version": "1.0.0",
            "supportedOS": "windows|mac",
        }, indent=2) + "\n", encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
