from functools import partial
import hashlib

from Corpus import git, read_tree
from NativeAcceptance.VerifyBatch import VerifyBatch
from NativeAcceptance.Records import ReadBytes, ReadJson


def LoadPinned(root, blob, expected):
    data = git(root, "cat-file", "blob", blob)
    if hashlib.sha256(data).hexdigest() != expected:
        raise ValueError("verification source differs from its pinned reader receipt")
    return data


def VerifyReader(root, application, output):
    if application == "solidworks":
        receipts = [(output, ReadJson(output / "receipt.json"))]
    else:
        summary = ReadJson(output / "summary.json")
        receipts = [(output / entry["directory"], ReadJson(output / entry["directory"] / "receipt.json")) for entry in summary["assets"] if entry["outcome"] == "decoded"]
    samples = []
    for directory, receipt in receipts:
        source = receipt["source"]
        if hashlib.sha256(ReadBytes(directory / "document.json", 64 * 1024 * 1024)).hexdigest() != receipt["neutral_sha256"]:
            raise ValueError("decoded output differs from its reader receipt")
        entries = read_tree(root, receipt["corpus_revision"])
        if entries.get(source["path"]) != source["git_blob"]:
            raise ValueError("native verification source is outside the pinned reader tree")
        samples.append({"path": source["path"], "sha256": source["sha256"], "configuration": receipt["options"].get("configuration"), "load": partial(LoadPinned, root, source["git_blob"], source["sha256"])})
    return VerifyBatch(root, application, samples, output / "NativeVerification.json")
