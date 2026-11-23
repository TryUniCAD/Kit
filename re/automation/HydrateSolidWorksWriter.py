from os import environ
from pathlib import Path
from re import fullmatch
from subprocess import run
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tests.Convert.Solidworks.Research.Frozen.ReadFrozen import ReadFrozen
from tests.Convert.Solidworks.Research.Frozen.ReadGitSource import HydrateFrozen
from tests.Convert.Solidworks.Research.Presentation.Frame.ReadFrameCase import ReadFrameCase
from tests.Convert.Solidworks.Research.Presentation.VerifyTree import ReadTreeFreeze


def main():
    manifests = (ReadFrozen(), ReadTreeFreeze(), ReadFrameCase()[0])
    objects = sorted({entry["git_blob"] for manifest in manifests for entry in manifest["files"]})
    if not objects or any(not fullmatch(r"[a-f0-9]{40}", value) for value in objects):
        raise ValueError("invalid frozen SOLIDWORKS source object inventory")
    request = ("\n".join(objects) + "\n").encode("ascii")
    HydrateFrozen(objects, request)
    checked = run(
        ["git", "cat-file", "--batch-check=%(objectname) %(objecttype)"],
        cwd=ROOT,
        env=dict(environ) | {"GIT_NO_LAZY_FETCH": "1"},
        input=request,
        capture_output=True,
        check=True,
        timeout=30,
    )
    if checked.stdout.decode("ascii").splitlines() != [f"{value} blob" for value in objects]:
        raise ValueError("frozen SOLIDWORKS source objects were not hydrated")
    print(f"Verified {len(objects)} pinned SOLIDWORKS source blobs")


if __name__ == "__main__":
    main()
