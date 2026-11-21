from argparse import ArgumentParser
from json import dumps
from pathlib import Path
from shutil import copyfile

from AuthorCurves import digest, require
from InspectSdkCachedDrawing import ORACLE, SCHEMA, STEMS, TOOLS, read_json


def freeze(host_builds, control_root, output):
    first, second = host_builds
    proof = read_json(first / "HostProof01.json")
    require((first / "HostProof01.json").read_bytes() == (second / "HostProof01.json").read_bytes()
            and (first / "NeutralRequest.json").read_bytes() == (second / "NeutralRequest.json").read_bytes(),
            "guarded host builds must agree on proof and neutral request")
    for root in host_builds:
        for key, name in STEMS.items():
            require(digest(root / name) == proof[key + "_sha256"], "host artifacts differ from guarded proof")
    control = read_json(control_root / "Control.json")
    output.mkdir()
    source = Path(__file__).resolve().parent
    tools = output / "Tools"
    tools.mkdir()
    for name in TOOLS:
        copyfile(source / name, tools / name)
    for index, root in enumerate(host_builds, 1):
        copyfile(root / "HostProof01.json", output / f"GuardedBuild{index}.json")
    for source_file, target in ((first / "NeutralRequest.json", output / "NeutralRequest.json"),
                                (control_root / "Control.json", output / "Control.json")):
        copyfile(source_file, target)
    controls = output / "Control"
    controls.mkdir()
    for key in STEMS:
        filename = control[key]["filename"]
        require(Path(filename).name == filename, "control filename must be one leaf")
        path = control_root / "Control" / filename
        require(digest(path) == control[key]["sha256"], "pristine control bytes changed")
        copyfile(path, controls / filename)
    job = {"schema": SCHEMA, "oracle_sha256": ORACLE, "heldout_inputs_read": 0,
           "neutral_sha256": digest(output / "NeutralRequest.json"), "control_sha256": digest(output / "Control.json"),
           "each_guarded_build_sha256": digest(output / "GuardedBuild1.json"),
           "tools_sha256": {name: digest(tools / name) for name in TOOLS}}
    trial = output / "Trial.json"
    trial.write_bytes((dumps(job, sort_keys=True, indent=2) + "\n").encode("utf-8"))
    return digest(trial)


def main():
    parser = ArgumentParser()
    parser.add_argument("--host-builds", type=Path, nargs=2, required=True)
    parser.add_argument("--control-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(freeze(args.host_builds, args.control_root, args.output))


if __name__ == "__main__":
    main()
