import os
import re
import tempfile
from pathlib import Path


def project_lock(project):
    if re.fullmatch(r"[A-Za-z0-9_-]{1,100}", project) is None:
        raise ValueError("Invalid project lease identifier")
    lease = (Path(tempfile.gettempdir()) / ("KitPlanning-" + project + ".lock")).open("a+")
    lease.seek(0)
    if os.name == "nt":
        import msvcrt
        if not lease.read(1):
            lease.write("0")
            lease.flush()
        lease.seek(0)
        msvcrt.locking(lease.fileno(), msvcrt.LK_NBLCK, 1)
    else:
        import fcntl
        fcntl.flock(lease.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    return lease
