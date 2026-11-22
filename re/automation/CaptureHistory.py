import argparse
import hashlib
from http.client import HTTPSConnection
import json
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote

from Corpus import asset_kind, git, read_tree

INPUT_PATHS = (
    "re/automation/PairedCaptures/",
    "re/automation/PairSpecs.json",
    "re/automation/Corpus.json",
    "re/Fusion/Study/thinextrudes-c1632bcb5efe/ordinary_rectangle_control.f3d",
    "re/solidworks/examples/.SLDPRT/example.SLDPRT",
)
CONTRACT = Path(__file__).with_name("CaptureLineage.json")

# the active authoring harness has its own pin alongside the preserved historical input
SOLIDWORKS_AUTHORING_PATH = (
    "re/automation/PairedCaptures/SolidWorksAuthoring/SolidWorksCapture.cs"
)

# only the reviewed authoring revision can replace the live entry at that path
SOLIDWORKS_AUTHORING_BLOB = "32f05b05db457b68f56091bf73bda00043b103c7"

ATTRIBUTION_INPUTS = {
    "re/automation/Corpus.json": (
        "c9ab93069474450d48ad56e11d23482c1a4f712f",
        "cc4877e647ce21904542913e1f85f181675c228f",
    ),
    "re/automation/PairedCaptures/SolidWorksAuthoring/BossWitnessReadback.cs": (
        "2cbadb2bace2225d84f778a10d455fe35e075319",
        "21d5c2e151a6894e562f6091038e769ef5293716",
    ),
    "re/automation/PairedCaptures/SolidWorksAuthoring/P02Readback.cs": (
        "210c13c2a66d239a391afcf4e53860d6515af96b",
        "655dfed84ac7e53ef62d7cbdb4efa53ac963f86c",
    ),
    "re/automation/PairedCaptures/SolidWorksAuthoring/RunBossWitness.ps1": (
        "d456572fa62aeba43c8f7a56972afd727ca0e150",
        "67f45c5be3109f08bc10a26a601e1ef5eee90396",
    ),
}


def unique_fields(pairs):
    value = dict(pairs)
    if len(value) != len(pairs):
        raise ValueError("duplicate lineage contract field")
    return value


def read_contract(path):
    raw = path.read_bytes()
    if not 0 < len(raw) <= 65536:
        raise ValueError("lineage contract exceeds its byte limit")
    value = json.loads(raw, object_pairs_hook=unique_fields)
    fields = {
        "lineage_version",
        "source_repository",
        "source_ref",
        "source_revision",
        "input_tree_sha256",
    }
    if not isinstance(value, dict) or set(value) != fields:
        raise ValueError("lineage contract fields differ")
    if type(value["lineage_version"]) is not int or value["lineage_version"] != 1:
        raise ValueError("unsupported lineage contract")
    patterns = {
        "source_repository": r"https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\.git",
        "source_ref": r"refs/heads/[A-Za-z0-9][A-Za-z0-9._/-]{0,255}",
        "source_revision": r"[0-9a-f]{40}",
        "input_tree_sha256": r"[0-9a-f]{64}",
    }
    if any(
        not isinstance(value[field], str) or re.fullmatch(pattern, value[field]) is None
        for field, pattern in patterns.items()
    ):
        raise ValueError("invalid lineage contract identity")
    return value


def input_tree(root, revision):
    if git(root, "rev-parse", "--is-shallow-repository").strip() != b"false":
        raise ValueError("historical lineage requires a complete commit and tree graph")
    if not isinstance(revision, str) or re.fullmatch(r"[0-9a-f]{40}", revision) is None:
        raise ValueError("lineage requires a full lowercase commit SHA")
    if (
        git(root, "rev-parse", "--verify", revision + "^{commit}").decode().strip()
        != revision
    ):
        raise ValueError("lineage revision is not an exact commit")
    rows = git(root, "ls-tree", "-rz", "--full-tree", revision, "--", *INPUT_PATHS)
    if len(rows) > 1024 * 1024:
        raise ValueError("lineage input tree exceeds its byte limit")
    result = {}
    for row in rows.split(b"\0"):
        if not row:
            continue
        metadata, name = row.split(b"\t", 1)
        mode, kind, checksum = metadata.decode("ascii").split()
        path = name.decode("utf-8")
        if mode not in {"100644", "100755"} or kind != "blob":
            raise ValueError("lineage inputs must remain regular tracked files")
        if path in result or re.fullmatch(r"[0-9a-f]{40}", checksum) is None:
            raise ValueError("ambiguous lineage input")
        result[path] = {"mode": mode, "git_blob": checksum}
    if not 1 <= len(result) <= 4096:
        raise ValueError("lineage input roster exceeds its file limit")
    return result


def tree_digest(entries):
    raw = json.dumps(entries, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(raw.encode("ascii")).hexdigest()


def bind_inputs(root, revision, source_revision, expected=None):
    original = input_tree(root, source_revision)
    observed = tree_digest(original)
    if expected is not None and observed != expected:
        raise ValueError("historical lineage input tree differs from its contract")
    current = input_tree(root, revision)
    current_digest = tree_digest(current)
    migrations = []
    binding = "identical_tracked_file_modes_and_blob_ids"
    if (
        expected is not None
        and SOLIDWORKS_AUTHORING_PATH in original
        and current.get(SOLIDWORKS_AUTHORING_PATH)
        == {"mode": "100644", "git_blob": SOLIDWORKS_AUTHORING_BLOB}
        and original[SOLIDWORKS_AUTHORING_PATH]["mode"] == "100644"
    ):
        current[SOLIDWORKS_AUTHORING_PATH] = original[SOLIDWORKS_AUTHORING_PATH]
        binding = "pinned_live_authoring_and_identical_historical_inputs"
    if expected is not None:
        for path, (before, after) in ATTRIBUTION_INPUTS.items():
            if (
                original.get(path) == {"mode": "100644", "git_blob": before}
                and current.get(path) == {"mode": "100644", "git_blob": after}
            ):
                current[path] = original[path]
                migrations.append({"path": path, "original_git_blob": before, "current_git_blob": after})
    if current != original:
        raise ValueError("current capture inputs differ from original lineage")
    result = {
        "lineage_revision": source_revision,
        "input_tree_sha256": observed,
        "bound_input_count": len(original),
        "binding": binding,
    }
    if migrations:
        result.update({
            "binding": "pinned_attribution_and_" + binding,
            "current_input_tree_sha256": current_digest,
            "attribution_migrations": migrations,
        })
    return result


def input_blobs(root, revision):
    original = input_tree(root, revision)
    allowed = {
        ".json",
        ".py",
        ".cs",
        ".ps1",
        ".md",
        ".txt",
        ".manifest",
        ".f3d",
        ".f3z",
        ".sldprt",
        ".sldasm",
    }
    if any(Path(path).suffix.lower() not in allowed for path in original):
        raise ValueError("historical input roster contains an unsupported artifact")
    blobs = {entry["git_blob"]: (revision, path) for path, entry in original.items()}
    for path in original:
        if not path.startswith(INPUT_PATHS[0]) or not path.endswith("/receipt.json"):
            continue
        introductions = (
            git(
                root,
                "log",
                "--format=%H",
                "--diff-filter=A",
                "--no-renames",
                revision,
                "--",
                path,
            )
            .decode("ascii")
            .splitlines()
        )
        if len(introductions) != 1:
            raise ValueError("capture has no unique original introduction")
        for name, entry in input_tree(root, introductions[0]).items():
            if name.startswith(INPUT_PATHS[0]) and Path(name).suffix in {".py", ".cs"}:
                blobs.setdefault(entry["git_blob"], (introductions[0], name))
    manifest_blob = original["re/automation/Corpus.json"]["git_blob"]
    manifest_raw = git(root, "cat-file", "blob", manifest_blob)
    if len(manifest_raw) > 32 * 1024 * 1024:
        raise ValueError("historical corpus manifest exceeds its byte limit")
    manifest = json.loads(manifest_raw, object_pairs_hook=unique_fields)
    if not isinstance(manifest, dict) or manifest.get("manifest_version") != 1:
        raise ValueError("unsupported historical corpus manifest")
    assets = manifest.get("assets")
    if not isinstance(assets, list) or not 1 <= len(assets) <= 10000:
        raise ValueError("historical corpus asset roster is invalid")
    corpus_tree = read_tree(root, manifest["source_revision"])
    for asset in assets:
        if not isinstance(asset, dict) or not isinstance(asset.get("path"), str):
            raise ValueError("historical corpus asset is invalid")
        kind = asset_kind(asset["path"])
        if kind is None or kind != asset.get("kind"):
            raise ValueError("historical corpus artifact kind differs")
        checksum = asset.get("git_blob")
        if (
            not isinstance(checksum, str)
            or re.fullmatch(r"[0-9a-f]{40}", checksum) is None
            or corpus_tree.get(asset["path"]) != checksum
        ):
            raise ValueError("historical corpus asset differs from its original tree")
        prefix_text = asset.get("prefix_hex")
        if (
            not isinstance(prefix_text, str)
            or re.fullmatch(r"[0-9a-f]{2,32}", prefix_text) is None
            or len(prefix_text) % 2
        ):
            raise ValueError("historical corpus prefix is invalid")
        prefix = bytes.fromhex(prefix_text)
        if prefix.startswith(
            (b"MZ", b"\x7fELF", b"\xcf\xfa\xed\xfe", b"\xfe\xed\xfa\xcf")
        ):
            raise ValueError("runtime software is not an allowed historical input")
        blobs.setdefault(checksum, (manifest["source_revision"], asset["path"]))
    if len(blobs) > 4096:
        raise ValueError("historical input object roster exceeds its limit")
    return blobs


def fetch_pinned_blob(root, contract, revision, path, checksum):
    repository = contract["source_repository"].removeprefix("https://github.com/").removesuffix(".git")
    connection = HTTPSConnection("raw.githubusercontent.com", timeout=30)
    try:
        connection.request("GET", f"/{repository}/{revision}/{quote(path)}")
        response = connection.getresponse()
        if response.status != 200:
            raise ValueError(f"sealed input {checksum} download returned HTTP {response.status}")
        data = response.read(100 * 1024 * 1024 + 1)
    finally:
        connection.close()
    if len(data) > 100 * 1024 * 1024:
        raise ValueError("sealed input exceeds the GitHub single file limit")
    observed = git(root, "hash-object", "--stdin", input_data=data).decode("ascii").strip()
    if observed != checksum:
        raise ValueError(f"sealed input {checksum} failed content verification")
    stored = git(root, "hash-object", "-w", "--stdin", input_data=data).decode("ascii").strip()
    if stored != checksum:
        raise ValueError("sealed input changed while storing its verified blob")


def hydrate_blobs(root, contract, blobs):
    blobs = dict(sorted(blobs.items()))
    result = (
        git(
            root,
            "cat-file",
            "--batch-check=%(objectname) %(objecttype)",
            input_data=("\n".join(blobs) + "\n").encode("ascii"),
        )
        .decode("ascii")
        .splitlines()
    )
    if len(result) != len(blobs):
        raise ValueError("historical object classification is incomplete")
    missing = []
    for checksum, row in zip(blobs, result, strict=True):
        fields = row.split()
        if (
            len(fields) != 2
            or fields[0] != checksum
            or fields[1] not in {"blob", "missing"}
        ):
            raise ValueError("historical input has an unexpected object type")
        if fields[1] == "missing":
            missing.append(checksum)
    for offset in range(0, len(missing), 64):
        batch = missing[offset : offset + 64]
        try:
            git(
                root, "-c", "protocol.version=2", "fetch", "--filter=blob:none",
                "--no-tags", "--no-write-fetch-head", "--recurse-submodules=no",
                contract["source_repository"], *batch,
            )
        except subprocess.CalledProcessError:
            for checksum in batch:
                revision, path = blobs[checksum]
                fetch_pinned_blob(root, contract, revision, path, checksum)
    observed = (
        git(
            root,
            "cat-file",
            "--batch-check=%(objectname) %(objecttype)",
            input_data=("\n".join(blobs) + "\n").encode("ascii"),
        )
        .decode("ascii")
        .splitlines()
    )
    if observed != [f"{checksum} blob" for checksum in blobs]:
        raise ValueError("historical input hydration is incomplete")
    return len(missing)


def hydrate_inputs(root, contract):
    original = input_tree(root, contract["source_revision"])
    hydrated = hydrate_blobs(
        root, contract, {original["re/automation/Corpus.json"]["git_blob"]: (contract["source_revision"], "re/automation/Corpus.json")}
    )
    return hydrated + hydrate_blobs(
        root, contract, input_blobs(root, contract["source_revision"])
    )


def fetch_history(root, contract):
    if contract != read_contract(CONTRACT):
        raise ValueError(
            "network hydration requires the bundled original lineage authority"
        )
    expected = f"{contract['source_revision']}\t{contract['source_ref']}\n".encode(
        "ascii"
    )
    observed = git(
        root,
        "ls-remote",
        "--exit-code",
        "--heads",
        contract["source_repository"],
        contract["source_ref"],
    )
    if observed != expected:
        raise ValueError("preserved source ref differs from its exact contract")
    git(
        root,
        "-c",
        "protocol.version=2",
        "fetch",
        "--filter=blob:none",
        "--no-tags",
        "--no-write-fetch-head",
        "--recurse-submodules=no",
        contract["source_repository"],
        contract["source_revision"],
    )
    entries = input_tree(root, contract["source_revision"])
    if tree_digest(entries) != contract["input_tree_sha256"]:
        raise ValueError("fetched historical input tree differs from its contract")
    hydrated = hydrate_inputs(root, contract)
    return {
        "source_revision": contract["source_revision"],
        "source_ref": contract["source_ref"],
        "input_tree_sha256": contract["input_tree_sha256"],
        "fetch_filter": "blob:none",
        "historical_checkout": False,
        "hydrated_input_blobs": hydrated,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Fetch original lineage metadata and pinned inputs"
    )
    parser.add_argument("command", choices=("fetch",))
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[2]
    )
    parser.add_argument("--contract", type=Path, default=CONTRACT)
    args = parser.parse_args()
    try:
        print(
            json.dumps(
                fetch_history(args.root, read_contract(args.contract)), sort_keys=True
            )
        )
    except (
        KeyError,
        OSError,
        TypeError,
        ValueError,
        subprocess.SubprocessError,
    ) as error:
        print(f"capture lineage metadata refused: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
