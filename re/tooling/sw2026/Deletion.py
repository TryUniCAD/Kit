from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive

WIN = "\\\\Mac\\Home\\Documents\\UniCAD\\Kit-worktrees\\sw2026\\"


def win(p):
    return WIN + str(Path(p).resolve().relative_to(ROOT)).replace("/", "\\")


def main():
    src = Path(sys.argv[1])
    out = Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    blob = src.read_bytes()
    arc = SldprtArchive.from_bytes(blob, src)
    names = [r.name for r in arc.records]
    files = []
    ext = src.suffix
    full = out / f"full_rebuilt{ext}"
    full.write_bytes(BuildSldprt([(r.name, r.data) for r in arc.records], template=blob))
    files.append(win(full))
    for i, n in enumerate(names):
        keep = [(r.name, r.data) for r in arc.records if r.name != n]
        p = out / f"drop_{i:02d}{ext}"
        p.write_bytes(BuildSldprt(keep, template=blob))
        files.append(win(p))
    (out / "names.json").write_text(json.dumps(names, indent=1))
    job = {"control": win(src), "files": files}
    (out / "job.json").write_text(json.dumps(job, indent=1))
    print(len(files))


if __name__ == "__main__":
    main()
