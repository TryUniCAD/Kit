from collections import Counter
from hashlib import sha256
from pathlib import Path, PureWindowsPath
from subprocess import run
import json
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "src"))

from convert import open_document
from convert.adapters.solidworks.Assembly.Assembly import DecodeNativeAsm
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Container import SldprtArchive, SldprtFormatError
from convert.adapters.solidworks.Core.Reading.ReadAdapter import NestedItemMap, NestedMap

BASE = "3b5caa3b599b2184f32260e8b383d15044946d5f"
FOLDER = Path("re/solidworks/examples/Single Turbo Dual Overhead Cam V8 - KDP - 2024")
OLD_PATH = r"D:\Archivos de diseño\Archivos_Motor_V8\TURBO\ENSAMBLAJE TURBO.SLDASM"
PARENT = ("ENSAMBLAJE DE MOTOR V8.SLDASM", "c1057dd8cf88808c017376e6f04bd50418bd9797f2ffb1d811a5836289b17a10")
KF = ("Turbo Assy KF.SLDASM", "c4b8f680d8bf3f20450c0c497991d251282b09f007290054cd963413b405c262")
ORIGINAL_IMPORTS = ("81c3740dec3f705435bd56519a46d08e020cea3b", "a145e762c2bb07d495a01c0e1a9962be54c9fe54")


def need(condition, error):
    if not condition:
        raise ValueError(error)


def git(*arguments):
    return run(("git", *arguments), check=True, cwd=ROOT, capture_output=True).stdout


def archive(case):
    name, pin = case
    path = ROOT / FOLDER / name
    source = path.read_bytes()
    need(sha256(source).hexdigest() == pin, "disclosed archive identity changed")
    return path, SldprtArchive.from_bytes(source)


def summarize(model, definition):
    files = {value.object_id: value for value in model.files}
    definitions = {value.object_id: value for value in model.definitions}
    children = Counter(
        PureWindowsPath(definitions[row.definition_id].source_path).name
        for row in model.occurrences if row.owner_definition_id == definition.object_id
    )
    return {
        "definition_id": definition.object_id,
        "file_ref": definition.file_id,
        "creation_time": files[definition.file_id].creation_time,
        "configuration_id": definition.configuration_id,
        "configuration": definition.configuration_name,
        "last_modified_stamp": definition.last_modified_stamp,
        "child_count": children.total(),
        "child_basenames": dict(sorted(children.items())),
    }


def expect_refusal(callable_value, error):
    try:
        callable_value()
    except SldprtFormatError as failure:
        need(error in str(failure), "unexpected strict refusal")
        return str(failure)
    raise ValueError("a known missing or different assembly was admitted")


def main():
    need(not git("diff", "--name-only", BASE, "--", "src"), "use the pinned SDK closure")
    need(not git("ls-files", "--others", "--exclude-standard", "--", "src"), "SDK closure has untracked files")
    parent_path, parent_archive = archive(PARENT)
    kf_path, kf_archive = archive(KF)
    need(not any(row.name.casefold() == PureWindowsPath(OLD_PATH).name.casefold()
                 for row in parent_path.parent.rglob("*")), "the local dependency must be evaluated directly")
    parent_model = DecodeNativeAsm(parent_archive)
    kf_model = DecodeNativeAsm(kf_archive)
    required, = (row for row in parent_model.definitions if row.source_path == OLD_PATH)
    occurrence, = (row for row in parent_model.occurrences if row.definition_id == required.object_id)
    available, = (row for row in kf_model.definitions if row.object_id == kf_model.root_definition_id)
    need(required.document_type == available.document_type == "ASSEMBLY" and not occurrence.suppressed,
         "the claimed missing assembly is not an actual active dependency")
    old, new = summarize(parent_model, required), summarize(kf_model, available)
    need(old["creation_time"] != new["creation_time"] and old["configuration"] != new["configuration"]
         and old["child_basenames"] != new["child_basenames"], "candidate identity requires a new investigation")
    refusal = expect_refusal(lambda: open_document(parent_path, strict=True, include_brep=False, include_tessellation=False),
                             "nested assembly mate source is unavailable: " + OLD_PATH)
    alternative = expect_refusal(lambda: NestedItemMap(parent_model, kf_model, NestedMap(parent_model, kf_model, required.object_id)),
                                 "root mappings")
    control = open_document(kf_path, strict=True, include_brep=False, include_tessellation=False)
    need(control.assembly is not None and control.source.sha256 == KF[1], "KF control lacks its own strict assembly identity")
    required_name = PureWindowsPath(OLD_PATH).name.casefold()
    for revision in (*ORIGINAL_IMPORTS, BASE):
        paths = git("ls-tree", "-rz", "--name-only", revision).decode().split("\x00")
        need(not any(PureWindowsPath(path).name.casefold() == required_name for path in paths),
             "fixture history contains the actual missing assembly name")
    manifest = json.loads(git("show", BASE + ":re/automation/Corpus.json"))
    need(not any(PureWindowsPath(row["path"]).name.casefold() == required_name for row in manifest["assets"]),
         "the evidence manifest binds the required assembly")
    return {
        "schema": "kit.solidworks.missing-example-turbo.v1",
        "sdk_revision": BASE,
        "sdk_src_tree": git("rev-parse", BASE + ":src").decode().strip(),
        "tool_sha256": sha256(HERE.read_bytes()).hexdigest(),
        "tracked_parent": {"path": (FOLDER / PARENT[0]).as_posix(), "sha256": PARENT[1],
                           "archive_version": ContainerMo(parent_archive.streams), "strict_refusal": refusal},
        "missing_owner": {**old, "recorded_path": OLD_PATH, "active_occurrence_id": occurrence.object_id,
                          "feature_id": occurrence.feature_id},
        "available_kf": {**new, "path": (FOLDER / KF[0]).as_posix(), "sha256": KF[1],
                         "archive_version": ContainerMo(kf_archive.streams), "strict_control_documents": len(control.assembly.documents),
                         "forced_nested_mapping_refusal": alternative},
        "fixture_revisions_without_path": [*ORIGINAL_IMPORTS, BASE],
        "manifest_source_revision": manifest["source_revision"],
        "manifest_has_exact_path": False,
        "native_processes": 0,
        "native_equivalence_credit": 0,
    }


if __name__ == "__main__":
    print(json.dumps(main(), indent=2, sort_keys=True, ensure_ascii=False))
