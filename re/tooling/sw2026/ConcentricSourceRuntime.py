from __future__ import annotations

from pathlib import Path
import json
from shutil import copyfile
import time

from AuthorCurves import Recorder,digest,require,write_json
from ConcentricMateEvidence import same_file

ORACLE="3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe"
CONTROL="c0472f9f42bf473a9073adb997180040b7767dfae93310610f77cff9509bec57"

def checked(path, expected, owner=None):
    require(path.is_file() and not path.is_symlink() and (owner is None or path.resolve().is_relative_to(owner.resolve()))
            and digest(path) == expected, "a pinned concentric source input changed")
    return path

def private_root(job, expected, identifier):
    import ctypes

    root = Path(job["guest_private_base"])
    drive = ctypes.windll.kernel32.GetDriveTypeW
    drive.argtypes = (ctypes.c_wchar_p,)
    drive.restype = ctypes.c_uint
    require(root.is_absolute() and root.resolve() == root and drive(root.anchor) == 3, "source privacy requires a canonical fixed guest drive")
    result = root / expected / identifier
    result.mkdir(parents=True, exist_ok=True)
    return result

def previous(root, identifier, phase, expected):
    path = root / "Progress" / identifier / phase / "Record.json"
    row = json.loads(path.read_bytes())
    require(row["packet_sha256"] == expected and row["case_id"] == identifier and row["phase"] == phase
            and row["stage"] == "passed" and row["passed"] is True, "a native source prerequisite is incomplete")
    return row

class SourceRecorder(Recorder):
    def __init__(self, path, job, publish):
        self.publish = publish
        self.last_public = float("-inf")
        super().__init__(path, job)

    def flush(self):
        super().flush()
        now = time.monotonic()
        if now - self.last_public >= 1:
            self.publish(progress_at=time.time())
            self.last_public = now

def identity(row):
    keys = ("process_id", "process_creation_filetime", "file_version", "sha256")
    require(row["version_matches"] and row["sha256"] == ORACLE and row["file_version"] == "34.5.2.0604"
            and type(row["process_creation_filetime"]) is int and row["process_creation_filetime"] > 0,
            "the source oracle does not match the pinned build")
    return {name: row[name] for name in keys}

def phase_paths(base, case, edited=False):
    folder = base / "Native" / ("Edited" if edited else "Source")
    return folder / (case["name"] + ".SLDASM"), folder / (case["child_name"] + ".SLDPRT")

def save_pair(author, controller, model, assembly, child, parent_path, child_path):
    from AuthorAssemblySources import save_owned_child

    parent_path.parent.mkdir(parents=True, exist_ok=False)
    child_status = list(author.rec.call("save exact owned native child", controller.save_as, child, child_path))
    require(child_status == [True, 0, 0] and same_file(author.get(child, "GetPathName"), child_path), "native child SaveAs failed or warned")
    saved_child = save_owned_child(author, assembly, child_path, 2, author.rec, parent_path.parent, basename=child_path.name)
    parent_status = list(author.rec.call("save exact owned native assembly after child", controller.save_as, model, parent_path))
    require(parent_status == [True, 0, 0] and digest(child_path) == saved_child["native_sha256"], "native parent SaveAs failed, warned or changed the synchronized child")
    return {"parent": {"status": parent_status, "sha256": digest(parent_path), "bytes": parent_path.stat().st_size},
            "child": {"status": saved_child["save_status"], "sha256": saved_child["native_sha256"], "bytes": saved_child["native_bytes"],
                      "update_stamp": saved_child["update_stamp"]}}

def assert_pairs(base, case, saved):
    require(set(saved) == {"source", "edited"}, "both ordinary native source states must remain locked")
    for key in saved:
        for role, path in zip(("parent", "child"), phase_paths(base, case, key == "edited"), strict=True):
            item = saved[key][role]
            require(item["status"] == [True, 0, 0] and checked(path, item["sha256"], base).stat().st_size == item["bytes"],
                    "an immutable native source sibling changed")

def control(seed, raw, publish):
    from InspectFresh import healthy, inspect

    result = {}
    def checkpoint():
        write_json(raw, result)
        if result.get("oracle_identity"):
            publish(identity=identity(result["oracle_identity"]), stage="native_control")
    inspect(seed, result=result, checkpoint=checkpoint)
    require(healthy(result) and identity(result["oracle_identity"]), "the bracketing native control failed")
    return {"identity": identity(result["oracle_identity"])}

def public_artifacts(saved):
    return {state: {role: {key: row[key] for key in ("sha256", "bytes")} for role, row in pair.items()}
            for state, pair in saved.items()}
