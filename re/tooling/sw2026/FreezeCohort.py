from __future__ import annotations

import argparse
import hashlib
import io
import json
import subprocess
from pathlib import Path


def git(root, *args, raw=False, data=None):
    result = subprocess.run(
        ["git", "-C", str(root), *args], input=data, capture_output=True, check=True
    ).stdout
    return result if raw else result.decode()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit-directory", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    revision = "f5953529e2114b5648cfe1e5341a83b1c2f0d9d6"
    freeze_path = root / "re/solidworks/v2026/heldout/ViewWriterFreeze.json"
    freeze = json.loads(freeze_path.read_text())
    frozen = {row["path"]: row for row in freeze["files"]}
    tree = {}
    for line in git(root, "ls-tree", "-r", revision).splitlines():
        info, name = line.split("\t", 1)
        mode, kind, object_id = info.split()
        if name in frozen or (name.startswith("src/") and name.endswith(".py")) or name in (
            "tests/__init__.py",
            "tests/Convert/__init__.py",
            "tests/Convert/Solidworks/__init__.py",
        ):
            if mode != "100644" or kind != "blob":
                raise ValueError((name, mode, kind))
            tree[name] = object_id
    names = sorted(tree)
    objects = io.BytesIO(git(root, "cat-file", "--batch", raw=True, data=("\n".join(tree[name] for name in names) + "\n").encode()))
    entries = []
    for name in names:
        object_id, kind, length = objects.readline().decode().split()
        raw = objects.read(int(length))
        if object_id != tree[name] or kind != "blob" or objects.read(1) != b"\n":
            raise ValueError(name)
        row = {"path": name, "git_blob": object_id, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
        if name in frozen and any(row[key] != frozen[name][key] for key in ("bytes", "sha256")):
            raise ValueError("original frozen source changed: " + name)
        entries.append(row)
    if objects.read() or set(frozen) - set(tree):
        raise ValueError("incomplete source inventory")
    imports = set()
    audit_files = []
    for path in sorted(args.audit_directory.glob("View*.json")):
        raw = path.read_bytes()
        report = json.loads(raw)
        audit_files.append({"name": path.name, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()})
        for item in report["module_reads"]:
            for marker in ("/re/tooling/sw2026/", "/src/", "/tests/"):
                if marker not in item:
                    continue
                source = Path(marker[1:] + item.split(marker, 1)[1])
                if source.suffix == ".pyc" and source.parent.name == "__pycache__":
                    source = source.parent.parent / (source.name.split(".cpython-", 1)[0] + ".py")
                if source.suffix == ".py":
                    imports.add(source.as_posix())
                break
    if len(audit_files) != 2 or imports - set(tree):
        raise ValueError("audit closure is incomplete")
    unchanged = []
    for prior in ("8672dd3340337a02cec5300bb838ebbc209063af", "dc74cd3385b3a8e3201617e90fbb54b7c258c3e8"):
        prior_tree = {}
        for line in git(root, "ls-tree", "-r", prior).splitlines():
            info, name = line.split("\t", 1)
            prior_tree[name] = info.split()[2]
        differences = [name for name in names if name not in frozen and prior_tree.get(name) != tree[name]]
        if differences:
            raise ValueError((prior, differences))
        unchanged.append({"revision": prior, "additional_source_files_compared": len(set(tree) - set(frozen)), "changed": 0})
    outputs = {}
    for receipt in ("EndHeldoutProcesses55d0", "CurveHeldoutProcessesAf6165", "ViewHeldoutProcessesFd08"):
        path = root / "re/solidworks/measurements/2026" / (receipt + ".json")
        report = json.loads(path.read_text())
        for row in report.get("cases", report.get("outputs", [])):
            name = row.get("name", row.get("request", {}).get("document", {}).get("name"))
            outputs[name] = {"bytes": row["bytes"], "sha256": row["sha256"], "receipt": path.relative_to(root).as_posix()}
    result = {
        "schema": "kit.sw2026.frozen-cohort-source.v1",
        "source_revision": revision,
        "source_tree": git(root, "rev-parse", revision + "^{tree}").strip(),
        "original_freeze_path": freeze_path.relative_to(root).as_posix(),
        "original_freeze_sha256": hashlib.sha256(freeze_path.read_bytes()).hexdigest(),
        "original_frozen_files": len(frozen),
        "source_file_count": len(entries),
        "src_python_count": sum(row["path"].startswith("src/") for row in entries),
        "audited_project_imports": len(imports),
        "audited_imports_outside_original_freeze": len(imports - set(frozen)),
        "audit_files": audit_files,
        "additional_sources_unchanged_at": unchanged,
        "files": entries,
        "measured_outputs": outputs,
        "retrospective_dependency_closure": True,
        "original_freezes_modified": False,
        "new_unseen_evidence": False,
        "native_acceptance_inherited": False,
        "policy": "Historical code only; original output hashes must reproduce exactly; current code is compared separately; any new writer behavior requires fresh independent inputs locked before its implementation",
    }
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({key: result[key] for key in ("source_file_count", "src_python_count", "audited_project_imports", "audited_imports_outside_original_freeze")}))


if __name__ == "__main__":
    main()
