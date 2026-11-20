# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tarfile
from tempfile import TemporaryDirectory, TemporaryFile

from CodecPromotion.Candidate import propose, replacements
from CodecPromotion.Contract import relative, validate, verify_file
from CodecPromotion.Evidence import evidence
from CodecPromotion.Qualification import observe
from InferenceInputs import parse_metadata, read_file

ROOT = Path(__file__).resolve().parents[2]


def git(directory, *args, **options):
    return subprocess.run(["git", "-C", str(directory), *args], check=True, **options)


def revision():
    return git(ROOT, "rev-parse", "HEAD", stdout=subprocess.PIPE).stdout.decode().strip()


def snapshot(tree, base):
    with TemporaryFile() as buffer:
        git(ROOT, "archive", base, "--", "src", "Cli", stdout=buffer)
        buffer.seek(0)
        with tarfile.open(fileobj=buffer) as archive:
            for member in archive:
                if not (member.isreg() or member.isdir()):
                    raise ValueError("codec snapshot must contain only regular source files")
                archive.extract(member, tree, filter="data")
    tree.chmod(0o755)


def regression(name):
    return f'''from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExe


# the public codec must reproduce independently measured values for the pinned samples
def CheckCodecCases() -> None:
    RootPath = FilePath(__file__).resolve().parents[3]
    _ = RunProcess(
        [
            PythonExe,
            str(RootPath / "re/automation/CodecPromotion/CheckContract.py"),
            str(RootPath / "re/automation/CodecPromotion/Cases/{name}.json"),
        ],
        cwd=RootPath,
        check=True,
        timeout=300,
    )
'''


def produce(args):
    if os.path.lexists(args.output):
        raise ValueError("output path already exists")
    spec = parse_metadata(read_file(args.request, 128 * 1024))
    if set(spec) != {"name", "base", "scope", "reference", "rule", "modules", "contract"} or not re.fullmatch("[A-Z][A-Za-z]{3,18}", spec["name"]):
        raise ValueError("invalid codec request or patch name")
    if not isinstance(spec["rule"], str) or not 1 <= len(spec["rule"].strip()) <= 3200:
        raise ValueError("supply a bounded independently documented format rule")
    if not re.fullmatch("sha256:[0-9a-f]{64}", args.image):
        raise ValueError("pin a locally installed qualification image by image ID")
    base = revision()
    if base != spec["base"]:
        raise ValueError("request base differs from the research checkout")
    finding, sources = evidence(args.store, args.job, args.receipt)
    note = relative(spec["reference"])
    if not note.startswith("re/") or not note.endswith(".md") or not git(ROOT, "ls-tree", base, "--", note, stdout=subprocess.PIPE).stdout:
        raise ValueError("cite a tracked format research note from the pinned revision")
    if finding["scope"] != spec["scope"]:
        raise ValueError("finding and request scopes differ")
    contract = spec["contract"]
    validate(contract, sources)
    modules = spec["modules"]
    if not isinstance(modules, list) or not 1 <= len(modules) <= 12 or len(set(modules)) != len(modules):
        raise ValueError("select one to twelve distinct codec modules")
    for path in modules:
        if not relative(path).startswith(("src/convert/adapters/", "src/convert/Formats/")) or not path.endswith(".py"):
            raise ValueError("only production codec modules may be proposed")
    with TemporaryDirectory() as folder:
        work = Path(folder)
        tree = work / "kit"
        snapshot(tree, base)
        originals = {p: (read_file(tree / p, 128 * 1024).decode() if (tree / p).exists() else "") for p in modules}
        inputs = []
        for index, case in enumerate(contract["cases"]):
            path = case["file"]
            blob = f"{base}:{path}"
            if int(git(ROOT, "cat-file", "-s", blob, stdout=subprocess.PIPE).stdout) > 128 * 1024 * 1024:
                raise ValueError("qualification sample exceeds 128 MiB")
            sample = work / (str(index) + Path(path).suffix)
            with sample.open("xb") as output:
                git(ROOT, "cat-file", "blob", blob, stdout=output)
            verify_file(sample, case["sha256"])
            sample.chmod(0o644)
            inputs.append((sample, case))
        reference = work / "reference" if contract["mode"] == "writer" else tree
        if reference != tree:
            snapshot(reference, base)
        before = [observe(tree, sample, contract, case, args.image, reference) for sample, case in inputs]
        if all(before):
            raise ValueError("existing codec already passes every independent case")
        candidate = replacements(
            parse_metadata(read_file(args.candidate, 512 * 1024)) if args.candidate else propose(finding, spec["rule"], originals),
            originals,
        )
        git(tree, "init", "-q")
        existing = [p for p in modules if (tree / p).is_file()]
        if existing:
            git(tree, "add", "--", *existing)
        base_tree = git(tree, "write-tree", stdout=subprocess.PIPE).stdout.decode().strip()
        # Keep Git metadata outside the candidate container mount.
        (tree / ".git").rename(work / "index.git")
        for path, source in candidate.items():
            target = tree / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(source, encoding="utf-8", newline="\n")
        for sample, case in inputs:
            if not observe(tree, sample, contract, case, args.image, reference):
                raise ValueError("candidate failed independent case: " + case["file"])
        (work / "index.git").rename(tree / ".git")
        name = spec["name"]
        category = "Readers" if contract["mode"] == "reader" else "Writers"
        additions = {
            f"tests/Research/CodecPromotion/{name}Tests.py": regression(name),
            f"re/automation/CodecPromotion/Cases/{name}.json": json.dumps(contract, indent=2) + "\n",
            f"Documentation/Changes/Research/{category}/Promotion/{name}.md": (
                f"# {name}\n\n{spec['rule']}\n\nPublic CLI {contract['mode']} qualification passed "
                f"{len(inputs)} pinned cases. The original codec passed {sum(before)}. "
                f"Format evidence: `{note}`. Base `{base}`, evidence receipt `{args.receipt}`, qualification image `{args.image}`.\n"
            ),
        }
        for path, text in additions.items():
            if git(ROOT, "ls-tree", base, "--", path, stdout=subprocess.PIPE).stdout:
                raise ValueError("generated artifact already exists: " + path)
            target = tree / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding="utf-8")
        git(tree, "add", "--", *modules, *additions)
        patch = git(tree, "diff", "--no-ext-diff", "--cached", "--full-index", base_tree, stdout=subprocess.PIPE).stdout
        if revision() != base or evidence(args.store, args.job, args.receipt) != (finding, sources):
            raise ValueError("checkout or receipt changed during qualification")
        with TemporaryDirectory(dir=args.output.parent) as publish:
            staged = Path(publish) / "candidate.patch"
            staged.write_bytes(patch)
            os.link(staged, args.output)
        return {"base": base, "receipt": args.receipt, "passed": len(inputs), "baseline_passed": sum(before),
                "patch": str(args.output), "sha256": hashlib.sha256(patch).hexdigest()}


def promote_scope(args, outcome):
    request = parse_metadata(read_file(args.codec_request, 128 * 1024))
    scope = outcome["scopes"].get(request["scope"])
    if not scope:
        raise ValueError("requested scope was not scheduled")
    jobs = [item for item in scope["jobs"] if item["kind"] in ("inference.fields", "inference.paired-gap")]
    if len(jobs) != 1 or not jobs[0].get("receipt"):
        raise ValueError("scope has no settled assessment receipt")
    return produce(argparse.Namespace(
        request=args.codec_request, image=args.codec_image, candidate=args.codec_candidate,
        output=args.codec_output, store=args.directory.resolve() / "Store",
        job=jobs[0]["id"], receipt=jobs[0]["receipt"],
    ))


def main():
    parser = argparse.ArgumentParser(description="Generate and qualify a reviewable reader or writer patch.", allow_abbrev=False)
    parser.add_argument("--store", required=True, type=Path)
    parser.add_argument("--job", required=True)
    parser.add_argument("--receipt", required=True)
    parser.add_argument("--request", required=True, type=Path)
    parser.add_argument("--image", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--candidate", type=Path, help="Review or retry supplied replacements without calling Codex")
    args = parser.parse_args()
    try:
        print(json.dumps(produce(args)))
    except (OSError, ValueError, KeyError, TypeError, SyntaxError, subprocess.SubprocessError) as error:
        parser.exit(1, f"codec promotion refused: {error}\n")


if __name__ == "__main__":
    main()
