from contextlib import contextmanager
import sys

from TraceCfgFinish import REVISION, source

IDENTITIES = (
    "Maps.ArchiveMaps", "Maps.MapEntry", "Maps.MapSnapshot",
    "Objects.ArchiveNode", "Objects.ExternalClass", "Objects.RuntimeClass",
)
SOURCE_REPOSITORY = "https://github.com/TryUniCAD/Kit.git"
SOURCE_PATHS = (
    "src/convert/__init__.py", "src/convert/adapters/__init__.py", "src/convert/adapters/Staging",
    "src/convert/adapters/base", "src/convert/adapters/registry", "src/convert/adapters/solidworks/__init__.py",
    "src/convert/adapters/solidworks/Archive", "src/convert/adapters/solidworks/Assembly/PlanarMates",
)


def sdk_name(name):
    return name == "convert" or name.startswith("convert.")


def archive_source():
    sys.path.insert(0, str(source.ROOT / "re/automation"))
    try:
        from CaptureHistory import hydrate_blobs
        from Corpus import git
    finally:
        sys.path.pop(0)
    entries = git(source.ROOT, "ls-tree", "-r", "-z", REVISION, "--", *SOURCE_PATHS)
    blobs = {}
    for entry in entries.rstrip(b"\0").split(b"\0"):
        info, path = entry.decode().split("\t", 1)
        mode, kind, oid = info.split()
        source.require(mode == "100644" and kind == "blob" and path.endswith(".py"),
                       "pinned Config-0 source tree contains an unexpected file")
        blobs[oid] = (REVISION, path)
    hydrate_blobs(source.ROOT, {"source_repository": SOURCE_REPOSITORY}, blobs)
    return git(source.ROOT, "archive", REVISION, "--", *SOURCE_PATHS)


class FinishSdkPin(source.PinnedSdk):
    def find_spec(self, fullname, path=None, target=None):
        spec = super().find_spec(fullname, path, target)
        if spec is None and sdk_name(fullname):
            raise ImportError(f"missing module in pinned Config-0 SDK: {fullname}")
        return spec


@contextmanager
def pinned_config():
    pin = FinishSdkPin(archive_source())
    current = {name: module for name, module in sys.modules.copy().items() if sdk_name(name)}
    shared = {source.ARCHIVE + name for name in IDENTITIES}
    source.require(shared <= current.keys(), "preload the current bounded codec before tracing Config-0")
    for name in shared:
        path, pinned_bytes = pin.modules[name]
        source.require((source.ROOT / path).read_bytes() == pinned_bytes,
                       f"cannot hand off a different archive identity class: {name}")
    for name in current.keys() - shared:
        del sys.modules[name]
    sys.meta_path.insert(0, pin)
    try:
        yield
    finally:
        sys.meta_path.remove(pin)
        for name in tuple(sys.modules):
            if sdk_name(name) and name not in current:
                del sys.modules[name]
        sys.modules.update(current)
