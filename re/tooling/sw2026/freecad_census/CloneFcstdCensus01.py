import argparse
from hashlib import sha256
import json
from pathlib import Path
from shutil import copyfile, copytree


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    source = args.source.resolve(strict=True)
    destination = args.destination.resolve()
    if destination.exists() or destination.is_relative_to(source):
        raise ValueError("choose an unused independent replay directory")
    manifest = json.loads((source / "CodeManifest01.json").read_bytes())
    for relative, row in manifest["files"].items():
        if digest(source / "CodeRoot" / relative) != row["sha256"]:
            raise ValueError("the frozen SDK source changed")
    if (
        digest(source / "AvailableNeutralSources.json")
        != "db7280b68f5bd30d5d3a3f8e3fe92b1ed335e7cd76786ae5cfbddb0064efa52c"
    ):
        raise ValueError("the disclosed roster changed")
    destination.mkdir(parents=True)
    copytree(source / "CodeRoot", destination / "CodeRoot")
    for name in ("CodeManifest01.json", "AvailableNeutralSources.json"):
        copyfile(source / name, destination / name)
    (destination / "Tools").mkdir()
    for name in (
        "CensusFcstdWorker01.py",
        "RunFcstdWriterCensus01.py",
        Path(__file__).name,
    ):
        copyfile(Path(__file__).resolve().parent / name, destination / "Tools" / name)
    for relative, row in manifest["files"].items():
        if digest(destination / "CodeRoot" / relative) != row["sha256"]:
            raise ValueError("the replay source differs")
    print(
        json.dumps(
            {
                "ready": True,
                "source_manifest_sha256": digest(destination / "CodeManifest01.json"),
                "native_processes_started": 0,
                "writer_outputs": 0,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
