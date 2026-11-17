from __future__ import annotations

import argparse
from base64 import b64decode
import json
import math
import os
from pathlib import Path
import subprocess
import sys

from AuthorCurves import digest, require, write_json
from AuthorRectangleAnchors import BOSS, CONTROL, ORACLE, ROLES, SKETCH
from InspectGeneratedRectangleAnchor import SCHEMA as NATIVE_SCHEMA, TOOLS as NATIVE_TOOLS, read_job


SCHEMA = "kit.sw2026.corner-anchor-heldout-preparation.v1"
SOURCE_LOCK = "7770ae975152aae0a6f211b5ab262541aeb15bea2861f96da9b80cd9cd432e7b"
DISCLOSED = "2dfc27e4a4ecc546142593bc42d2e147bc163b6d402d97a9d16af94da8043a30"
PRIVATE_ROOT = Path(r"C:\KitRectangleAnchorSources01")
BUILDER = "re/tooling/sw2026/RectangleAnchorPartProcess.py"
TOOLS = (*NATIVE_TOOLS, Path(__file__).name)


def checked(path, sha):
    require(digest(path) == sha, f"frozen anchor prerequisite changed: {path.name}")
    return path


def load(path):
    return json.loads(path.read_bytes())


def new_json(path, value):
    require(not path.exists(), f"preserve existing anchor evidence: {path.name}")
    write_json(path, value)
    return digest(path)


def verify(root, sha):
    plan = load(checked(root / "Method.json", sha))
    require(plan["schema"] == SCHEMA and plan["slot"] == "H01" and plan["oracle_sha256"] == ORACLE,
            "expected the original held-out corner slot")
    require(Path(__file__).resolve().parent == root / "Tools" and set(plan["tools_sha256"]) == set(TOOLS),
            "expected the complete frozen anchor method")
    for name, expected in plan["tools_sha256"].items():
        checked(root / "Tools" / name, expected)
    checked(root / "Control.SLDPRT", CONTROL)
    lock = load(checked(root / "SourceLock.json", SOURCE_LOCK))
    require(lock["controls_healthy"] and lock["writer_output_count"] == 0 and lock["distinct_processes"] == 6
            and lock["oracle_sha256"] == ORACLE and lock["cases"]["H01"]["family"] == "corner",
            "pre-writer corner source qualification differs")
    disclosed = load(checked(root / "DisclosedNative.json", DISCLOSED))
    require(disclosed["passed"] and disclosed["native_constraint_and_tree_parity"] and disclosed["controls_healthy"]
            and not disclosed["heldout_acceptance"], "expected the qualified disclosed corner comparison")
    manifest = load(checked(root / "CodeManifest.json", plan["code_manifest_sha256"]))
    require(manifest["files_sha256"].get("re/tooling/sw2026/InspectGeneratedRectangleAnchor.py")
            == plan["tools_sha256"]["InspectGeneratedRectangleAnchor.py"]
            and BUILDER in manifest["files_sha256"], "expected the unchanged observer and tracked guarded writer")
    return plan, lock, manifest


def verify_code(root, manifest):
    code = root / "CodeRoot"
    current = {p.relative_to(code).as_posix() for p in code.rglob("*.py")}
    require(current == set(manifest["files_sha256"]), "the exact anchor writer source set changed")
    for name, sha in manifest["files_sha256"].items():
        relative = Path(name)
        require(not relative.is_absolute() and ".." not in relative.parts and not (code / relative).is_symlink(),
                "anchor source escaped its frozen code root")
        checked(code / relative, sha)
    return code


def checked_case(case):
    require(set(case) == {"kind", "width_m", "height_m", "depth_m", "edit_width_m", "edit_height_m"}
            and case["kind"] == "corner"
            and all(type(value) in (int, float) and math.isfinite(value) and 0.001 < value < 0.25
                    for name, value in case.items() if name != "kind")
            and case["width_m"] != case["edit_width_m"] and case["height_m"] != case["edit_height_m"],
            "sealed recipe must independently change the corner's driving dimensions")
    return case


def release_recipe(root, method_sha, lock):
    require(os.name == "nt", "the original recipe is released from the Windows-local source store")
    require(not (root / "Candidate.SLDPRT").exists() and not (root / "SourceRecord.json").exists(),
            "recipe release precedes generated output and comparison inputs")
    specs = checked(PRIVATE_ROOT / "SourceRecipes.json", lock["sealed_specifications_sha256"])
    case = checked_case(load(specs)["H01"])
    receipt = {"slot": "H01", "case": case, "method_sha256": method_sha,
               "source_lock_sha256": SOURCE_LOCK, "sealed_specifications_sha256": digest(specs),
               "native_sources_opened": False, "comparison_observations_opened": False}
    return {"recipe_sha256": new_json(root / "SelectedRecipe.json", receipt), "native_sources_opened": False}


def make_request(code, case):
    sys.path[:0] = [str(code), str(code / "src")]
    from tests.Convert.Solidworks.Research.FreshPartInput import MakePartInput
    from tests.Convert.Solidworks.Research.Presentation.MakeTreeInput import MakeTreeInput

    width, height, depth = (case[key] for key in ("width_m", "height_m", "depth_m"))
    vertices = [[0.0, 0.0], [width, 0.0], [width, height], [0.0, height]]
    request = MakeTreeInput(MakePartInput(vertices, depth, "H01CornerModel"))
    request["native_plane_roles"] = True
    request["rectangle_anchor"] = "corner"
    request["document"].update(configuration_name="Default", sketch_name=SKETCH, extrusion_name=BOSS,
                               rectangle_dimensions={"width_text_m": [width / 2, -0.3 * height],
                                                     "height_text_m": [1.3 * width, height / 2], "route_centerline": False})
    request["presentation"]["folder_order"] = list(request["presentation"]["folder_names"])
    return request


def generate(root, method_sha, plan, lock, manifest, recipe_sha):
    code = verify_code(root, manifest)
    recipe = load(checked(root / "SelectedRecipe.json", recipe_sha))
    require(recipe["slot"] == "H01" and recipe["method_sha256"] == method_sha
            and recipe["source_lock_sha256"] == SOURCE_LOCK and not recipe["native_sources_opened"]
            and not recipe["comparison_observations_opened"] and recipe["sealed_specifications_sha256"] == lock["sealed_specifications_sha256"],
            "selected recipe does not come from the original source lock")
    require(all(not (root / name).exists() for name in ("Candidate.SLDPRT", "GenerationFreeze.json", "SourceRecord.json", "Job.json")),
            "generate afresh before attaching comparisons")
    request = make_request(code, checked_case(recipe["case"]))
    request_file = root / "Request.json"
    request_sha = new_json(request_file, request)
    results = []
    for ordinal in range(2):
        run = subprocess.run([sys.executable, "-I", "-B", str(code / BUILDER)], input=request_file.read_bytes(),
                             cwd=code, capture_output=True, timeout=120)
        with (root / f"Writer{ordinal}.stderr").open("xb") as fp:
            fp.write(run.stderr)
        require(run.returncode == 0, "guarded held-out corner generation failed")
        results.append(json.loads(run.stdout))
    first, second = results
    require(first == second and first["writer_output_count"] == 1 and first["new_origin_relations"] == 1
            and first["input_runtime_file_access_attempts"] == 0 and not first["native_acceptance"],
            "the two guarded corner builds disagree")
    content = b64decode(first["native"].pop("artifact_base64"), validate=True)
    with (root / "Candidate.SLDPRT").open("xb") as writer:
        writer.write(content)
    candidate = checked(root / "Candidate.SLDPRT", first["native"]["sha256"])
    require(candidate.stat().st_size == first["native"]["bytes"], "generated corner length differs")
    proof_sha = new_json(root / "Construction.json", first)
    frozen = {"method_sha256": method_sha, "code_manifest_sha256": plan["code_manifest_sha256"], "recipe_sha256": recipe_sha,
              "request_sha256": request_sha, "construction_sha256": proof_sha, "candidate_sha256": digest(candidate),
              "guarded_builds": 2, "native_source_payloads_read": False, "comparison_observations_read": False}
    return {"generation_freeze_sha256": new_json(root / "GenerationFreeze.json", frozen),
            "native_source_payloads_read": False, "writer_output_count": 1}


def attach(root, method_sha, plan, lock, generation_sha):
    require(os.name == "nt", "the original corner observations stay bound to the Windows-local source")
    freeze = load(checked(root / "GenerationFreeze.json", generation_sha))
    require(freeze["method_sha256"] == method_sha and freeze["code_manifest_sha256"] == plan["code_manifest_sha256"]
            and freeze["guarded_builds"] == 2 and not freeze["native_source_payloads_read"] and not freeze["comparison_observations_read"],
            "candidate was not frozen before source access")
    for name, field in (("Candidate.SLDPRT", "candidate_sha256"), ("Request.json", "request_sha256"), ("Construction.json", "construction_sha256")):
        checked(root / name, freeze[field])
    proof = load(root / "Construction.json")
    require(proof["input_runtime_file_access_attempts"] == 0 and proof["native"]["sha256"] == freeze["candidate_sha256"],
            "the generated candidate lacks its runtime guard")
    recipe = load(checked(root / "SelectedRecipe.json", freeze["recipe_sha256"]))
    require(not (root / "SourceRecord.json").exists() and not (root / "Job.json").exists(), "preserve the first native comparison")
    identities = lock["cases"]["H01"]
    files = load(checked(PRIVATE_ROOT / "H01Artifacts.json", identities["native_artifact_manifest_sha256"]))
    require(set(files) == set(ROLES), "the declared original corner artifacts changed")
    heldout = PRIVATE_ROOT / "corner"
    checked(heldout / "Author" / "Record.json", identities["source_record_sha256"])
    for role, row in files.items():
        path = checked(heldout / "Author" / (role + ".SLDPRT"), row["sha256"])
        require(path.stat().st_size == row["bytes"] and row["status"] == [True, 0, 0], "native corner source save differs")
    source_record = checked(heldout / "Reopen" / "Record.json", identities["reopen_record_sha256"])
    with (root / "SourceRecord.json").open("xb") as out:
        out.write(source_record.read_bytes())
    job = {"schema": NATIVE_SCHEMA, "oracle_sha256": ORACLE, "heldout_acceptance": False,
           "case": recipe["case"], "method_sha256": method_sha, "source_lock_sha256": SOURCE_LOCK,
           "generation_freeze_sha256": generation_sha,
           "tools_sha256": {name: plan["tools_sha256"][name] for name in NATIVE_TOOLS},
           "inputs_sha256": {"Control.SLDPRT": CONTROL, "Candidate.SLDPRT": freeze["candidate_sha256"],
                             "SourceRecord.json": identities["reopen_record_sha256"]}}
    job_path = root / "Job.json"
    job_sha = new_json(job_path, job)
    read_job(job_path, job_sha)
    return {"job_sha256": job_sha, "locked_observations_attached": True,
            "source_artifact_count": len(files), "native_processes_started": 0}


def main():
    parser = argparse.ArgumentParser(description="Prepare the original pre-writer locked corner rectangle native comparison")
    parser.add_argument("phase", choices=("verify", "release-recipe", "generate", "attach"))
    parser.add_argument("root", type=Path)
    parser.add_argument("--method-sha256", required=True)
    parser.add_argument("--recipe-sha256")
    parser.add_argument("--generation-sha256")
    args = parser.parse_args()
    root = args.root.resolve(strict=True)
    plan, lock, manifest = verify(root, args.method_sha256)
    if args.phase == "verify":
        verify_code(root, manifest)
        result = {"verified": True, "hidden_recipe_opened": False, "native_source_payloads_read": False}
    elif args.phase == "release-recipe":
        verify_code(root, manifest)
        result = release_recipe(root, args.method_sha256, lock)
    elif args.phase == "generate":
        result = generate(root, args.method_sha256, plan, lock, manifest, args.recipe_sha256)
    else:
        result = attach(root, args.method_sha256, plan, lock, args.generation_sha256)
    print(json.dumps(result, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
