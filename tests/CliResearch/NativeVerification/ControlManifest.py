from hashlib import sha256 as DigestBytes
from json import dumps as EncodeJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess

from tests.CliResearch.ResearchRoot import ReadHead, ResearchRoot

# semantic comparison needs the independently authored control rather than the historical default manifest
KAssetPath = (
    "re/automation/PairedCaptures/P03/fusion-8d53584027ff/P03-fusion-baseline-a.f3d"
)


# a minimal pinned corpus keeps integration evidence tied to the candidate checkout objects
def ControlManifest(TmpPath: FilePath) -> FilePath:
    RootPath = ResearchRoot()
    GitBlob = RunProcess(
        ["git", "-C", str(RootPath), "rev-parse", "--verify", "HEAD:" + KAssetPath],
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    ).stdout.strip()
    ArchiveBytes = RunProcess(
        ["git", "-C", str(RootPath), "cat-file", "blob", GitBlob],
        capture_output=True,
        check=True,
        timeout=30,
    ).stdout
    Manifest = {
        "manifest_version": 1,
        "source_revision": ReadHead(RootPath),
        "assets": [
            {
                "path": KAssetPath,
                "kind": "native",
                "format": "f3d",
                "git_blob": GitBlob,
                "size_bytes": len(ArchiveBytes),
                "sha256": DigestBytes(ArchiveBytes).hexdigest(),
                "prefix_hex": ArchiveBytes[:16].hex(),
            }
        ],
    }
    ManifestPath = TmpPath / "PinnedControl.json"
    _ = ManifestPath.write_text(EncodeJson(Manifest), encoding="utf-8")
    return ManifestPath
