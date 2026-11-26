from functools import partial
import hashlib
import json

from Corpus import git, read_tree
from NativeAcceptance.VerifyBatch import VerifyBatch
from NativeAcceptance.Records import FileHash, ReadBytes, ReadJson


def LoadPinned(root, blob, expected):
    data = git(root, "cat-file", "blob", blob)
    if hashlib.sha256(data).hexdigest() != expected:
        raise ValueError("verification source differs from its pinned reader receipt")
    return data


def VerifyReader(root, application, output, *, directories=None):
    sdk_sources = {str(path.relative_to(root)): FileHash(path) for path in sorted((root / "src").rglob("*.py"))}
    sdk_digest = hashlib.sha256(json.dumps(sdk_sources, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    if application == "solidworks":
        if directories is None:
            directories = [output]
    else:
        summary = ReadJson(output / "summary.json")
        directories = [output / entry["directory"] for entry in summary["assets"] if entry["outcome"] == "decoded"]
    samples = []
    trees = {}
    for directory in directories:
        receipt = ReadJson(directory / "receipt.json")
        source = receipt["source"]
        if receipt["sdk_sources_sha256"] != sdk_digest:
            raise ValueError("SDK sources changed after reader artifact publication")
        if hashlib.sha256(ReadBytes(directory / "document.json", 64 * 1024 * 1024)).hexdigest() != receipt["neutral_sha256"]:
            raise ValueError("decoded output differs from its reader receipt")
        revision = receipt["corpus_revision"]
        if revision not in trees:
            trees[revision] = read_tree(root, revision)
        entries = trees[revision]
        if entries.get(source["path"]) != source["git_blob"]:
            raise ValueError("native verification source is outside the pinned reader tree")
        samples.append({"path": source["path"], "sha256": source["sha256"], "configuration": receipt["options"].get("configuration"), "neutral_path": directory / "document.json", "neutral_sha256": receipt["neutral_sha256"], "load": partial(LoadPinned, root, source["git_blob"], source["sha256"])})
    return VerifyBatch(root, application, samples, output / "NativeVerification.json")
