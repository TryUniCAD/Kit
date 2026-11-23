from pathlib import Path as FilePath
from subprocess import run as RunProcess

from tests.Research.Custody.CaptureRetryWitness import KRepository


# a fresh git repository gives each hydration process its own object store and transport configuration
def GitFixture(Directory: FilePath) -> FilePath:
    Target = Directory / "Target"
    Remote = Directory / "Empty.git"
    _ = RunProcess(
        ("git", "init", str(Target)), check=True, capture_output=True, timeout=30
    )
    _ = RunProcess(
        ("git", "init", "--bare", str(Remote)),
        check=True,
        capture_output=True,
        timeout=30,
    )
    _ = RunProcess(
        ("git", "config", f"url.{Remote.as_uri()}.insteadOf", KRepository),
        cwd=Target,
        check=True,
        capture_output=True,
        timeout=30,
    )
    return Target
