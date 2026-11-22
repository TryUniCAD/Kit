from argparse import ArgumentParser
from json import dumps, loads
from pathlib import Path
from subprocess import check_output
import sys

from FilletModel import require
from FilletModelPacket import FILES, OWNED_TOOLS, SCHEMA, generation_cases, load_job, root_value
from FilletPacket import CONTROL, SHARED_TOOLS, job_bytes
from FilletStockPacket import INTENT_SHA, NAMES, ORACLE_AUTHORITY, pinned, sha, write_new

HERE = Path(__file__).resolve().parent
SW = HERE.parent
ROOT = SW.parents[2]
sys.path.insert(0, str(ROOT / "src"))

from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeader
from convert.adapters.solidworks.Container.Container import SldprtArchive


def git(*args):
    return check_output(("git", "-C", str(ROOT), *args))


def prepare(args):
    output = args.output.resolve()
    root = root_value(args.guest_root)
    require(not output.exists() and not output.is_relative_to(ROOT) and output.parent.is_dir(),
            "model fillet packet needs a fresh external directory")
    probe = git("rev-parse", "HEAD").decode().strip()
    construction = args.construction.resolve(strict=True).read_bytes()
    evidence = loads(construction)
    writer = evidence["source_head"]
    tree = git("rev-parse", writer + ":src").decode().strip()
    cases = generation_cases(evidence, root, writer, tree)
    tools = evidence["tools"]
    require(isinstance(tools, dict)
            and "re/tooling/sw2026/edge_fillet_source/cold/BuildColdFillet.py" in tools
            and all(name.startswith("re/tooling/sw2026/") and name.endswith(".py")
                    and sha(git("show", f"{writer}:{name}")) == pin for name, pin in tools.items()),
            "the generation tool hashes must match the frozen writer commit")
    data = {"Spec.json": pinned(HERE / "DisclosedFilletInputs.json", INTENT_SHA),
            "Control.SLDPRT": pinned(args.control.resolve(strict=True), CONTROL),
            "Construction.json": construction}
    for name in NAMES:
        row = cases[name]
        path = args.candidates.resolve(strict=True) / f"{name}.SLDPRT"
        raw = pinned(path, row["sha256"])
        archive = SldprtArchive.from_bytes(raw)
        header = ReadHeader(archive.require("Contents/Config-0-ModelHeader"), 19000)
        require(header.SelfFile.PathValue == row["encoded_locator"]
                and header.SelfFile.KindValue == 2 and len(raw) == row["bytes"],
                f"{name} does not bind its constructed locator and zero input accesses")
        require({key: sha(value) for key, value in archive.streams.items()}
                == {key: value["sha256"] for key, value in row["streams"].items()},
                f"{name} does not reproduce its guarded clear stream identities")
        data[f"Generated/{path.name}"] = raw
    for home, names in ((HERE, OWNED_TOOLS), (SW, SHARED_TOOLS)):
        for name in names:
            tool = home / name
            data[f"Tool/{name}"] = git("show", f"{probe}:{tool.relative_to(ROOT).as_posix()}")
            require(data[f"Tool/{name}"] == tool.read_bytes(), f"oracle tool diverges from frozen commit: {name}")
    require(set(data) == FILES, "model fillet packet inventory differs")
    output.mkdir(exist_ok=False)
    (output / "Tool").mkdir(exist_ok=False)
    (output / "Generated").mkdir(exist_ok=False)
    for name, raw in data.items():
        write_new(output / name, raw)
    job = job_bytes({"schema": SCHEMA, "oracle": ORACLE_AUTHORITY, "guest_root": str(root),
                     "writer_commit": writer, "writer_tree": tree, "probe_commit": probe,
                     "files": {name: {"sha256": sha(raw), "bytes": len(raw)} for name, raw in data.items()}})
    manifest = output / "ModelJob.json"
    write_new(manifest, job)
    load_job(manifest, sha(job))
    return {"job": str(manifest), "job_sha256": sha(job), "files": len(data), "native_processes_started": 0}


def main():
    parser = ArgumentParser(description="freeze two disclosed model-only fillets for the exact native oracle")
    parser.add_argument("--candidates", type=Path, required=True)
    parser.add_argument("--construction", type=Path, required=True)
    parser.add_argument("--control", type=Path, required=True)
    parser.add_argument("--guest-root", required=True)
    parser.add_argument("--output", type=Path, required=True)
    print(dumps(prepare(parser.parse_args()), sort_keys=True))


if __name__ == "__main__":
    main()
