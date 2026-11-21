import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def execute(command, log):
    log.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(command, text=True, capture_output=True)
    log.with_suffix(".stdout.txt").write_text(result.stdout)
    log.with_suffix(".stderr.txt").write_text(result.stderr)
    if result.returncode:
        raise ValueError("isolated SDK process failed: " + str(log))
    return json.loads(log.read_text())


def check(args):
    args.output.mkdir(parents=True, exist_ok=False)
    manifest = json.loads(args.manifest.read_text())
    for root_name in ("baseline", "candidate"):
        for name, expected in manifest[root_name]["files_sha256"].items():
            if digest(getattr(args, root_name) / name) != expected:
                raise ValueError("frozen executable source changed: " + name)
    for name, expected in manifest["tools_sha256"].items():
        if digest(Path(__file__).parent / name) != expected:
            raise ValueError("frozen audit tool changed: " + name)
    cohort = json.loads(args.cohort.read_text())
    tool_root = Path(__file__).parent
    results, count = [], 0
    mutations = (
        "CopiedRoot",
        "CopiedMember",
        "CopiedHelper",
        "ForeignHelper",
        "StrippedPublicMember",
        "StrippedMembers",
        "StrippedHelper",
        "ForeignEnvironment",
        "ForeignProfile",
        "CopiedComponent",
        "CopiedDepth",
        "CopiedScope",
        "ForeignScope",
        "UnusedCutDepth",
        "WrongEnd",
        "LostAxisRelation",
        "BrokenNotePair",
        "AuthoredLight",
        "ExtraFeature",
        "UnqualifiedVersion",
    )
    for item in cohort["cases"]:
        trial = Path(item["trial"])
        if digest(trial) != item["trial_sha256"]:
            raise ValueError("disclosed trial identity changed")
        job = json.loads(trial.read_text())
        source = trial.parent / job["control_file"]
        if digest(source) != item["source_sha256"]:
            raise ValueError("declared disclosed source changed")
        prefix = [
            sys.executable,
            "-B",
            str(tool_root / "InspectThruTree.py"),
            "--source",
            str(source),
            "--source-sha256",
            item["source_sha256"],
        ]
        records = {}
        for root_name in ("baseline", "candidate"):
            for mode in ("path", "bytes"):
                path = args.output / item["id"] / (root_name + mode + ".json")
                command = (
                    prefix
                    + ["--root", str(getattr(args, root_name)), "--output", str(path)]
                    + (["--from-bytes"] if mode == "bytes" else [])
                )
                records[root_name + mode] = execute(command, path)
                count += 1
        for mode in ("path", "bytes"):
            before, after = records["baseline" + mode], records["candidate" + mode]
            if (
                before["status"] != "unqualified"
                or after["status"] != "ordinary_through_all_source_profile"
                or before["portable_sha256"] != after["portable_sha256"]
                or before["public_ids"] != after["public_ids"]
            ):
                raise ValueError(
                    "new presentation altered the existing complete portable document"
                )
            tree = after["tree"]
            rows = {row["native_object_id"] for row in tree["rows"]}
            helpers = {row["stored_node_id"] for row in tree["configuration_helpers"]}
            retained = set(tree["retained_public_ids"])
            if (
                len(retained) != 28
                or rows | helpers != retained
                or rows & helpers
                or len(tree["root_ids"]) != 21
                or len(tree["member_ids"]) != 6
            ):
                raise ValueError(
                    "presentation did not preserve the complete original identity closure"
                )
            if (
                tree["source_conversion_qualified"]
                or tree["provenance_qualified"]
                or tree["continuous_automatic_scope_qualified"]
                or tree["full_native_tree_qualified"]
            ):
                raise ValueError("presentation overclaimed unsupported acceptance")
        checked = []
        selected = (
            mutations
            if item["id"] == "D01"
            else ("CopiedRoot", "CopiedHelper", "ForeignScope", "StrippedMembers")
        )
        for mutation in selected:
            path = args.output / item["id"] / "Mutations" / (mutation + ".json")
            result = execute(
                prefix
                + [
                    "--root",
                    str(args.candidate),
                    "--output",
                    str(path),
                    "--mutation",
                    mutation,
                ],
                path,
            )
            if (
                result["status"] != "unqualified"
                or not result["all_public_ids_retained"]
            ):
                raise ValueError("malformed source ownership was admitted or filtered")
            checked.append(
                {
                    "mutation": mutation,
                    "record_sha256": digest(path),
                    "diagnostic": result["diagnostic"],
                }
            )
            count += 1
        results.append(
            {
                "id": item["id"],
                "source_sha256": item["source_sha256"],
                "public_ids": records["candidatepath"]["public_ids"],
                "root_ids": records["candidatepath"]["tree"]["root_ids"],
                "member_ids": records["candidatepath"]["tree"]["member_ids"],
                "helper_ids": [
                    row["stored_node_id"]
                    for row in records["candidatepath"]["tree"]["configuration_helpers"]
                ],
                "portable_fields_unchanged": True,
                "mutations": checked,
                "path_read_sha256": digest(
                    args.output / item["id"] / "candidatepath.json"
                ),
                "bytes_read_sha256": digest(
                    args.output / item["id"] / "candidatebytes.json"
                ),
            }
        )
        if digest(source) != item["source_sha256"]:
            raise ValueError("source changed during audit")
    compatibility = []
    for variant in (0, 1):
        records = []
        for root_name in ("baseline", "candidate"):
            path = args.output / "Compatibility" / (root_name + str(variant) + ".json")
            records.append(
                execute(
                    [
                        sys.executable,
                        "-B",
                        str(tool_root / "throughpresentation/Compat.py"),
                        "--root",
                        str(getattr(args, root_name)),
                        "--variant",
                        str(variant),
                        "--output",
                        str(path),
                    ],
                    path,
                )
            )
            count += 1
        if records[0] != records[1]:
            raise ValueError("old caller or complete generated output changed")
        compatibility.append(records[0])
    result = {
        "status": "passed_source_presentation_only",
        "baseline_revision": manifest["baseline"]["source_revision"],
        "manifest_sha256": digest(args.manifest),
        "cohort_sha256": digest(args.cohort),
        "fresh_process_count": count,
        "cases": results,
        "old_caller_compatibility": compatibility,
        "native_oracle_used": False,
        "held_out_accessed": False,
        "source_conversion_qualified": False,
        "public_writer_promoted": False,
    }
    (args.output / "Result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            {
                "status": result["status"],
                "fresh_process_count": count,
                "result_sha256": digest(args.output / "Result.json"),
            }
        )
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--cohort", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    check(parser.parse_args())


if __name__ == "__main__":
    main()
