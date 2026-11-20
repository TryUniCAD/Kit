import hashlib
import json
import os
from pathlib import Path
import secrets
import stat
from contextlib import contextmanager


def ReadBytes(path, limit=256 * 1024 * 1024):
    path = Path(path)
    before = path.lstat()
    if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or getattr(before, "st_file_attributes", 0) & 0x400:
        raise ValueError("verification input must be a regular file without links")
    with path.open("rb") as stream:
        opened = os.fstat(stream.fileno())
        data = stream.read(limit + 1)
        after = os.fstat(stream.fileno())
    final = path.lstat()
    fields = ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns")
    if len(data) > limit or any(len({getattr(item, field) for item in (before, opened, after, final)}) != 1 for field in fields):
        raise ValueError("verification input changed or exceeded its byte limit")
    return data


def ReadJson(path):
    return json.loads(ReadBytes(path, 16 * 1024 * 1024))


def WriteJson(path, value):
    path = Path(path)
    data = (json.dumps(value, sort_keys=True, allow_nan=False) + "\n").encode()
    if len(data) > 16 * 1024 * 1024:
        raise ValueError("verification report exceeds 16 MiB")
    temporary = path.with_name("." + path.name + secrets.token_hex(16))
    try:
        with temporary.open("xb") as stream:
            os.chmod(temporary, 0o600)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def FileHash(path):
    return hashlib.sha256(ReadBytes(path)).hexdigest()


def Endpoint():
    return Path.home() / ".kit" / "verification" / "fusion"


@contextmanager
def LockEndpoint(path):
    with Path(path).open("a+b") as stream:
        if os.name == "nt":
            import msvcrt

            stream.seek(0)
            msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            yield
        finally:
            if os.name == "nt":
                stream.seek(0)
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
