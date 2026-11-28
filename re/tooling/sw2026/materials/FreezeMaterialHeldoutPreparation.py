from argparse import ArgumentParser
from base64 import b64decode
from copy import deepcopy
from io import BytesIO
import json
from math import isclose, prod
from pathlib import Path, PurePosixPath
import re
from subprocess import check_output, run
import sys
from tarfile import open as open_tar


HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
MATERIALS = "re/tooling/sw2026/materials/"
WORKER = MATERIALS + "PrepareMaterialHeldout.py"
FREEZER = MATERIALS + HERE.name
BASE = "389f52b3c11d39cff370afd4907456898a0af4a9"
SDK_TREE = "1763b025e85f91c4a1a0512c7149cd098a886c0b"
SCHEMA = "kit.sw2026.neutral-material-preparation-method.v1"
INPUT_SCHEMA = "kit.sw2026.neutral-material-preparation.v1"
SCOPE = "origin-owned-physical-material"
PENDING = ["assigned_appearance", "numeric_catalog_identity", "material_tree"]
GUARD = "tests/Convert/Solidworks/Research/ConstructionGuard.py"
TEST_INITS = ("tests/__init__.py", "tests/Convert/__init__.py", "tests/Convert/Solidworks/__init__.py",
              "tests/Convert/Solidworks/Research/__init__.py")
PROBE = MATERIALS + "BuildAssignedMaterialProbe.py"
RELATED = (
    "re/tooling/sw2026/SdkBlindPartSettings.py", "re/tooling/sw2026/SdkRectDimRejects.py",
    "re/tooling/sw2026/SdkBlindPartChecks.py",
    "re/tooling/sw2026/body/NamedOutput/AnchoredProof/Harness01/CheckAnchoredGraph.py",
    PROBE,
)
EVIDENCE = (
    "re/solidworks/measurements/2026/AssignedMaterialPhysicalProbeBuild01.json",
    "re/solidworks/measurements/2026/AssignedMaterialPhysicalProbeNative01.json",
    "re/solidworks/measurements/2026/SdkAnchoredNamedPartNative02.json",
)
NEEDED = (WORKER, FREEZER, GUARD, *RELATED)
CHANGE_PATHS = {
    WORKER, FREEZER,
    "Documentation/Changes/Solidworks/Inspection/Materials/SolidworksMaterialNeutralPreparation.md",
    "re/solidworks/records/AssignedMaterialNeutralPreparation2026.md",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(value):
    from hashlib import sha256

    return sha256(value).hexdigest()


def encode(value, *, pretty=True):
    return (json.dumps(value, sort_keys=True, indent=2 if pretty else None,
                       separators=None if pretty else (",", ":"), ensure_ascii=True, allow_nan=False) + "\n").encode()


def store(path, content):
    with path.open("xb") as file:
        file.write(content)


def checked(path, value):
    require(type(value) is str and re.fullmatch("[a-f0-9]{64}", value), "expected a pinned SHA-256 digest")
    require(path.is_file() and not path.is_symlink(), "pinned method member is unavailable")
    raw = path.read_bytes()
    require(digest(raw) == value, "pinned method member digest differs")
    return raw


def git(*args):
    return check_output(("git", "-C", str(ROOT), *args))


def blob(rev, path):
    return git("cat-file", "blob", rev + ":" + path)


def commit_check(revision):
    require(re.fullmatch("[a-f0-9]{40}", revision)
            and git("merge-base", BASE, revision).decode().strip() == BASE
            and set(git("diff", "--name-only", BASE, revision).decode().splitlines()) == CHANGE_PATHS
            and git("rev-parse", revision + ":src").decode().strip() == SDK_TREE,
            "freeze requires the committed method on the exact unaffected SDK base")
    require(blob(revision, FREEZER) == HERE.read_bytes(), "running freezer differs from the committed method")
    for path in (*RELATED, GUARD, *EVIDENCE):
        require(blob(revision, path) == blob(BASE, path), "an existing proof dependency changed")


def restore(revision, root):
    requested = ("src", *NEEDED, *TEST_INITS)
    listing = git("ls-tree", "-r", "-z", revision, *requested)
    entries = [row.decode().split("\t", 1) for row in listing.split(b"\x00") if row.endswith(b".py")]
    require(all(metadata.split()[:2] in (["100644", "blob"], ["100755", "blob"]) for metadata, _ in entries),
            "only regular tracked Python files belong in this freeze")
    expected = {name for _, name in entries}
    require(set(NEEDED) <= expected, "a tracked method dependency is missing")
    manifest = {}
    with open_tar(fileobj=BytesIO(git("archive", revision, "--", "src"))) as archive:
        for member in archive:
            name = member.name
            if name not in expected:
                continue
            relative = PurePosixPath(name)
            require(member.isfile() and name not in manifest and not relative.is_absolute()
                    and ".." not in relative.parts and str(relative) == name,
                    "frozen source contains an unsafe archive member")
            data = archive.extractfile(member).read()
            path = root.joinpath(*relative.parts)
            path.parent.mkdir(parents=True, exist_ok=True)
            store(path, data)
            manifest[name] = digest(data)
    for name in sorted(item for item in expected if not item.startswith("src/")):
        data = blob(revision, name)
        path = root.joinpath(*PurePosixPath(name).parts)
        path.parent.mkdir(parents=True, exist_ok=True)
        store(path, data)
        manifest[name] = digest(data)
    require(set(manifest) == expected, "frozen source inventory differs from the tracked commit")
    return manifest


def synthetic_request(kind):
    width, height, depth, edited = {
        "corner": (0.01814, 0.022673, 0.00827, 0.01192),
        "center": (0.027631, 0.01525, 0.01071, 0.00731),
    }[kind]
    name = "Synthetic" + kind.title()
    first, second = ("A", "B") if kind == "corner" else ("B", "A")
    return {"schema": INPUT_SCHEMA, "scope": SCOPE,
            "case": {"id": name, "kind": kind, "configuration": "Default", "width_m": width, "height_m": height,
                     "depth_m": depth, "edited_depth_m": edited, "first_material_key": first, "second_material_key": second},
            "catalog": {"A": {"database_name": "Authored Alloy.sldmat", "name": "Alloy Alpha", "density_kg_m3": 2863.75},
                        "B": {"database_name": "Authored Steel.sldmat", "name": "Steel Gamma", "density_kg_m3": 7027.5}},
            "target": {"path": "C:\\KitSyntheticMaterialPreparation\\" + name + ".SLDPRT", "saved_at": 1795000120}}


def worker(root, request):
    return run((sys.executable, "-I", "-B", str(root / WORKER), str(root)),
               cwd=root, input=encode(request, pretty=False), capture_output=True, timeout=75, check=False)


def expect_result(process, request):
    require(process.returncode == 0 and not process.stderr, process.stderr.decode())
    answer = json.loads(process.stdout)
    contents = b64decode(answer.pop("artifact_base64"), validate=True)
    case = request["case"]
    kind = case["kind"]
    anchor = answer["anchor"]
    require(answer["scope"] == SCOPE and answer["pending_domains"] == PENDING
            and len(contents) == answer["candidate_bytes"] and digest(contents) == answer["candidate_sha256"]
            and answer["request_sha256"] == digest(encode(request, pretty=False))
            and answer["baseline_sha256"] != answer["candidate_sha256"]
            and answer["runtime_input_or_cad_access_attempts"] == 0
            and not answer["native_acceptance"] and not answer["full_source_preserved"]
            and anchor["actual_model_origin_bound"] and anchor["all_three_driver_owners_preserved"]
            and anchor["written_owner_readback"] and anchor["boundary_lines"] == 4
            and (anchor["point_count"], anchor["line_count"], anchor["coincidence_count"]) ==
            ((5, 4, 1) if kind == "corner" else (6, 6, 3)),
            "guarded worker did not retain both native origin and physical part ownership")
    first = request["catalog"][case["first_material_key"]]
    second = request["catalog"][case["second_material_key"]]
    observed = answer["typed_owners"]
    require(observed["part_density"] == observed["config_density"] == first["density_kg_m3"]
            and observed["config_identity"] == first["database_name"][:-7] + "|" + first["name"]
            and observed["exact_linked_streams"] == 3, "typed material field replay differs")
    width, height = (case[key] for key in ("width_m", "height_m"))
    for name, (depth, entry) in {
        "initial": (case["depth_m"], first), "swapped": (case["depth_m"], second),
        "depth_edit": (case["edited_depth_m"], first), "swapped_depth_edit": (case["edited_depth_m"], second),
    }.items():
        expected = answer["expectations"][name]
        require(expected["solid_body_count"] == 1 and
                isclose(expected["mass_kg"], prod((width, height, depth, entry["density_kg_m3"])), rel_tol=1e-13)
                and expected["density_kg_m3"] == entry["density_kg_m3"]
                and expected["geometry"]["com"] == ([width / 2, height / 2, depth / 2] if kind == "corner"
                                                   else [0.0, 0.0, depth / 2]),
                "separate case prediction disagrees on mass or anchor-sensitive centroid")
    return answer


def synthetic_preflight(root):
    positives = {}
    for kind in ("corner", "center"):
        request = synthetic_request(kind)
        first, second = (worker(root, request) for _ in range(2))
        first_result = expect_result(first, request)
        require(first_result == expect_result(second, request) and first.stdout == second.stdout,
                "independent guarded subprocesses did not regenerate exactly")
        positives[kind] = first_result
    invalid = (
        ("full_source", ("scope",), "full-source", "full source preservation requires"),
        ("unknown_anchor", ("case", "kind"), "offset", "explicit corner or center intent"),
        ("ambiguous_material", ("case", "second_material_key"), "A", "two different material selectors"),
        ("boolean_dimension", ("case", "width_m"), True, "finite SI lengths"),
        ("body_override", ("case", "body_material"), "A", "explicit corner or center intent"),
        ("numeric_catalog_id", ("catalog", "A", "catalog_id"), 246, "two-token declared catalog"),
        ("catalog_locator", ("catalog", "A", "database_name"), "C:Other.sldmat", "catalog filename"),
        ("unexpected_appearance", ("catalog", "A", "appearance"), [0.3, 0.7, 0.2], "two-token declared catalog"),
        ("wrong_native_location", ("target", "path"), r"\Mac\Home\Candidate.SLDPRT", "exact Windows-local SLDPRT locator"),
    )
    refusals = []
    for name, keys, value, expected in invalid:
        request = deepcopy(synthetic_request("corner"))
        owner = request
        for key in keys[:-1]:
            owner = owner[key]
        owner[keys[-1]] = value
        process = worker(root, request)
        require(process.returncode != 0 and not process.stdout and expected in process.stderr.decode(),
                "malformed input did not stop before candidate publication: " + name)
        refusals.append(name)
    return {"schema": "kit.sw2026.material-preparation-synthetic-preflight.v1",
            "synthetic_controls": positives, "independent_guarded_processes": len(invalid) + 4,
            "refusals": refusals, "native_processes": 0, "heldout_credit": 0}


def freeze(revision, packet):
    commit_check(revision)
    packet.mkdir(exist_ok=False)
    code = packet / "CodeRoot"
    files = restore(revision, code)
    preflight = encode(synthetic_preflight(code))
    store(packet / "SyntheticPreflight.json", preflight)
    manifest = encode({"python_sha256": files})
    store(packet / "CodeManifest.json", manifest)
    method = encode({
        "schema": SCHEMA, "revision": revision, "base_revision": BASE, "sdk_tree": SDK_TREE, "scope": SCOPE,
        "pending_domains": PENDING, "entry": WORKER, "entry_sha256": files[WORKER],
        "code_manifest_sha256": digest(manifest), "synthetic_preflight_sha256": digest(preflight),
        "prior_evidence_sha256": {name: digest(blob(BASE, name)) for name in EVIDENCE},
        "native_processes": 0, "protected_inputs_read": 0,
    })
    store(packet / "Method.json", method)
    return {"method_sha256": digest(method), "code_manifest_sha256": digest(manifest),
            "entry_sha256": files[WORKER], "synthetic_preflight_sha256": digest(preflight), "python_files": len(files)}


def verify(packet, method_sha):
    method = json.loads(checked(packet / "Method.json", method_sha))
    require(method["schema"] == SCHEMA and method["base_revision"] == BASE and method["sdk_tree"] == SDK_TREE
            and method["scope"] == SCOPE and method["entry"] == WORKER and method["pending_domains"] == PENDING
            and method["native_processes"] == method["protected_inputs_read"] == 0,
            "frozen method scope or base differs")
    preflight = json.loads(checked(packet / "SyntheticPreflight.json", method["synthetic_preflight_sha256"]))
    require(set(preflight["synthetic_controls"]) == {"corner", "center"} and len(preflight["refusals"]) == 9
            and preflight["heldout_credit"] == preflight["native_processes"] == 0, "synthetic authority differs")
    files = json.loads(checked(packet / "CodeManifest.json", method["code_manifest_sha256"]))["python_sha256"]
    code = packet / "CodeRoot"
    require(not code.is_symlink() and set(NEEDED) <= set(files) and files[WORKER] == method["entry_sha256"]
            and HERE.read_bytes() == (code / FREEZER).read_bytes(), "frozen runtime closure differs")
    seen = {path.relative_to(code).as_posix() for path in code.rglob("*") if path.is_file() or path.is_symlink()}
    require(seen == set(files), "frozen runtime inventory changed")
    for name, sha in files.items():
        relative = PurePosixPath(name)
        path = code.joinpath(*relative.parts)
        require(not relative.is_absolute() and ".." not in relative.parts and str(relative) == name
                and not any(item.is_symlink() for item in (path, *path.parents) if item.is_relative_to(code)),
                "invalid frozen runtime member")
        checked(path, sha)
    return {"verified": True, "python_files": len(files), "method_sha256": method_sha,
            "protected_inputs_read": 0, "native_processes": 0}


def main():
    parser = ArgumentParser()
    parser.add_argument("action", choices=("freeze", "verify", "preflight"))
    parser.add_argument("packet", type=Path)
    parser.add_argument("--revision")
    parser.add_argument("--method-sha256")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.action == "freeze":
        result = freeze(args.revision, args.packet.resolve())
    else:
        packet = args.packet.resolve(strict=True)
        result = verify(packet, args.method_sha256)
        if args.action == "preflight":
            if args.output is None:
                parser.error("--output is required for a new local synthetic preflight")
            raw = encode(synthetic_preflight(packet / "CodeRoot"))
            store(args.output, raw)
            result["local_synthetic_preflight_sha256"] = digest(raw)
    sys.stdout.buffer.write(encode(result))


if __name__ == "__main__":
    main()
