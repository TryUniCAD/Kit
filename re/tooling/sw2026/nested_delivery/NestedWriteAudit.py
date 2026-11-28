from hashlib import sha256
import os
from pathlib import Path


ACCESS_MODE_MASK = getattr(os, "O_ACCMODE", os.O_RDONLY | os.O_WRONLY | os.O_RDWR)


def require(condition, why):
    if not condition:
        raise ValueError(why)


def digest(data):
    return sha256(data).hexdigest()


def snapshot(directory):
    result = {}
    for entry in sorted(directory.rglob("*")):
        relative = entry.relative_to(directory).as_posix()
        if entry.is_symlink():
            result[relative] = {"symlink": str(entry.readlink())}
        elif entry.is_dir():
            result[relative] = {"directory": True}
        else:
            data = entry.read_bytes()
            result[relative] = {"bytes": len(data), "sha256": digest(data)}
    return result


class Audit:
    def __init__(self, area, target, last, names, mode):
        self.area = area
        self.target = target
        self.last = last
        self.names = frozenset(names)
        self.mode = mode
        self.active = True
        self.attempts = []
        self.published = []
        self.staged_write_attempts = []
        self.injected = False

    def inspect(self, event, args):
        if not self.active:
            return
        if event.startswith(("subprocess.", "socket.", "ctypes.", "winreg.")) or event in (
            "os.exec", "os.system", "os.startfile", "os.posix_spawn", "os.fork",
        ):
            self.attempts.append(event)
            raise PermissionError("unexpected external process or data access")
        if event == "open":
            path, mode, flags = args
            if not isinstance(path, (str, bytes)):
                self.attempts.append("descriptor open")
                raise PermissionError("unexpected descriptor open")
            location = Path(os.fsdecode(path))
            if location.is_absolute() and location.is_relative_to(self.area):
                if mode is None and location.is_dir() and location.parent == self.target.parent:
                    return
                if flags & ACCESS_MODE_MASK == os.O_WRONLY and flags & os.O_EXCL and location.name in self.names:
                    if location.parent != self.target.parent:
                        self.staged_write_attempts.append(location.name)
                        if self.mode == "stage-denied" and location.name == self.last.name:
                            raise PermissionError("controlled staged companion failure")
                    return
            self.attempts.append(("file open", location.name, mode, flags, location.is_relative_to(self.area)))
            raise PermissionError("publication attempted to read an input or write outside its destination")
        if event in ("os.scandir", "os.listdir"):
            path = args[0]
            if isinstance(path, int):
                return
            if path is None or not Path(os.fsdecode(path)).is_relative_to(self.area):
                self.attempts.append(event)
                raise PermissionError("publication inspected a directory outside its destination")
        if event not in ("os.link", "os.rename"):
            return
        destination = Path(os.fsdecode(args[1]))
        if destination.parent != self.target.parent or destination.name not in self.names:
            return
        self.published.append(destination.name)
        if self.mode == "publish-denied" and destination == self.last:
            raise PermissionError("controlled final companion failure")
        if self.mode == "publish-race" and destination == self.target and not self.injected:
            self.injected = True
            with self.last.open("xb") as output:
                output.write(b"peer owns the last nested companion")
