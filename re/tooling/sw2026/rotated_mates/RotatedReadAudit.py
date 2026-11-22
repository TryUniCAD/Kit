from collections import Counter
from contextlib import contextmanager
from os import O_CREAT, O_RDWR, O_TRUNC, O_WRONLY, fsdecode
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[4]
SCOPE = "cold_parallel_distance_coincident"


@contextmanager
def source_only(paths, rules=()):
    expected = {path.resolve() for path in paths}
    schemas = {path.resolve() for path in rules}
    directories = {path.parent for path in expected}
    accessed = Counter()
    enabled = True

    def audit(event, values):
        if not enabled:
            return
        if (event in ("subprocess.Popen", "os.startfile", "os.system", "os.fork", "ctypes.dlopen", "ctypes.dlsym")
                or event.startswith(("os.exec", "os.spawn", "os.posix_spawn", "socket."))):
            raise PermissionError(f"unexpected reader runtime: {event}")
        if event not in ("open", "os.listdir", "os.scandir"):
            return
        location = values[0] if values else None
        path = Path(fsdecode(location)).resolve() if isinstance(location, (str, bytes)) else None
        caller = sys._getframe(1)
        import_code = caller.f_code.co_filename == "<frozen importlib._bootstrap_external>"
        if event == "open":
            if import_code and caller.f_code.co_name == "get_data" and path is not None and path.suffix in (".py", ".pyc"):
                return
            if values[2] & (O_WRONLY | O_RDWR | O_CREAT | O_TRUNC):
                raise PermissionError(f"unexpected write access during inspection: {path}")
            if path in expected or path in schemas:
                accessed[path.name] += 1
                return
            raise PermissionError(f"unexpected reader file access: {path}")
        if event in ("os.listdir", "os.scandir"):
            if import_code or path in directories:
                return
            raise PermissionError(f"unexpected reader directory access: {path}")


    sys.addaudithook(audit)
    try:
        yield accessed
    finally:
        enabled = False
