from http.client import HTTPConnection as LocalConnection
from importlib import import_module as ImportModule
from pathlib import Path as FilePath
from sys import argv as Arguments, path as ImportPaths
from unittest.mock import patch as Patch

# the loopback witness requires the same sealed repository and revision path on every retry
KRepository = "https://github.com/Test/Fixture.git"

# the loopback witness observes the original immutable revision in each request
KRevision = "1" * 40

# an encoded path proves retries preserve the requested fixture identity
KFixturePath = "fixture folder/model.json"


# the process redirects only the transport while the real downloader and git keep their normal behavior
def OpenLoopback(HostName: str, **Options: float) -> LocalConnection:
    assert HostName == "raw.githubusercontent.com"
    return LocalConnection("127.0.0.1", int(Arguments[3]), timeout=Options["timeout"])


# fixture recovery calls the same missing object hydration path as merge queue setup
def RunHydration() -> None:
    ImportPaths.insert(
        0, str(FilePath(__file__).resolve().parents[3] / "re/automation")
    )
    CaptureHistory = ImportModule("CaptureHistory")
    Checksum = Arguments[2]
    with Patch.object(CaptureHistory, "HTTPSConnection", OpenLoopback):
        print(
            CaptureHistory.hydrate_blobs(
                FilePath(Arguments[1]),
                {"source_repository": KRepository},
                {Checksum: (KRevision, KFixturePath)},
            )
        )


if __name__ == "__main__":
    RunHydration()
