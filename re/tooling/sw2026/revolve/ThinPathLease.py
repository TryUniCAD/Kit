from contextlib import contextmanager
from os import name as os_name
from pathlib import Path
from shutil import rmtree
from stat import FILE_ATTRIBUTE_REPARSE_POINT, S_ISDIR, S_ISREG
from uuid import uuid4

MARKER = ".kit-thin-suite-owner"


def measured_target(locator):
    target = Path(locator)
    root = target.parent.parent
    if (
        os_name != "nt"
        or not target.is_absolute()
        or root.parent != Path(target.anchor)
        or root == root.parent
        or target.parent.name != "Candidates"
        or ".." in target.parts
        or target.suffix.casefold() != ".sldprt"
    ):
        raise ValueError("thin suite requires the measured Windows candidate locator")
    return target


def owned_stat(path, expected_type):
    metadata = path.lstat()
    if (
        not expected_type(metadata.st_mode)
        or getattr(metadata, "st_file_attributes", 0) & FILE_ATTRIBUTE_REPARSE_POINT
        or metadata.st_ino <= 0
    ):
        raise ValueError("thin suite lease requires an ordinary local object identity")
    return metadata.st_dev, metadata.st_ino


def prove_lease(root, token):
    identity = owned_stat(root, S_ISDIR)
    marker = root / MARKER
    owned_stat(marker, S_ISREG)
    if marker.read_text(encoding="ascii") != token:
        raise ValueError("thin suite lease marker differs")
    return identity


@contextmanager
def own_root(root):
    root.mkdir(mode=0o700)
    identity = owned_stat(root, S_ISDIR)
    token = uuid4().hex
    with (root / MARKER).open("x", encoding="ascii") as marker:
        marker.write(token)
    try:
        yield token
    finally:
        if prove_lease(root, token) != identity:
            raise ValueError("thin suite will not clean a replaced root")
        rmtree(root)
