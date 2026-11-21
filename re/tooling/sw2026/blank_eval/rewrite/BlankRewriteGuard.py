import os
from pathlib import Path


class OutputGuard:
    def __init__(self, root):
        self.root = root.resolve()
        self.active = False
        self.written = set()
        self.directories = {self.root}
        self.operations = []
        self.denied = []

    def fail(self, event, path=None):
        self.denied.append({"event": event, "path": str(path) if path is not None else None})
        raise RuntimeError("unexpected input, template, process or external output access")

    def owned(self, value):
        return Path(os.fsdecode(value)).resolve().is_relative_to(self.root)

    def event(self, event, args):
        if not self.active:
            return
        if event == "open":
            value, mode, flags = args
            if isinstance(value, (str, bytes)):
                path = Path(os.fsdecode(value)).resolve()
                writing = isinstance(mode, str) and any(c in mode for c in "wax+") or mode is None and flags & (os.O_CREAT | os.O_WRONLY | os.O_RDWR)
                if path.is_relative_to(self.root):
                    if writing:
                        self.written.add(path)
                        self.operations.append("output_write")
                        return
                    if path in self.written:
                        self.operations.append("computed_output_read")
                        return
                    if path in self.directories and path.is_dir():
                        self.operations.append("owned_output_directory_open")
                        return
            self.fail(event, value)
        if event == "os.mkdir":
            if self.owned(args[0]):
                self.directories.add(Path(args[0]).resolve())
                return
            self.fail(event, args[0])
        if event in ("os.listdir", "os.scandir"):
            if type(args[0]) is int:
                identity = os.fstat(args[0])
                for directory in self.directories:
                    if directory.exists():
                        other = directory.stat()
                        if (identity.st_dev, identity.st_ino) == (other.st_dev, other.st_ino):
                            self.operations.append("owned_output_directory_scan")
                            return
            elif self.owned(args[0]):
                self.operations.append("owned_output_directory_scan")
                return
            self.fail(event, args[0])
        if event in ("os.rename", "os.link"):
            if self.owned(args[0]) and self.owned(args[1]):
                source, target = (Path(value).resolve() for value in args[:2])
                if source in self.written:
                    self.written.add(target)
                    self.operations.append("output_publish")
                    return
            self.fail(event)
        if event in ("os.remove", "os.rmdir"):
            if args[1] != -1 and type(args[1]) is int:
                if type(args[0]) is str and Path(args[0]).name == args[0]:
                    identity = os.fstat(args[1])
                    for directory in self.directories:
                        if directory.exists():
                            other = directory.stat()
                            if (identity.st_dev, identity.st_ino) == (other.st_dev, other.st_ino):
                                return
                self.fail(event, args[0])
            if self.owned(args[0]):
                return
            self.fail(event, args[0])
        if event.startswith(("subprocess.", "socket.", "winreg.", "ctypes.")) or event in ("os.exec", "os.posix_spawn", "os.spawn", "os.system"):
            self.fail(event)
