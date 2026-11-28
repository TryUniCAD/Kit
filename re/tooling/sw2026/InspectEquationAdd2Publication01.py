from __future__ import annotations

import argparse
import json
from pathlib import Path

import AuthorEquationSources01 as baseline


class PublicationAuthor(baseline.EquationAuthor):
    def publication(self, manager, stage):
        count = int(self.eq(manager, "GetCount", 1))
        baseline.require(
            0 <= count <= 2,
            "the equation publication probe has an unexpected row count",
        )
        result = {"stage": stage, "count": count, "rows": []}
        for index in range(count):
            text = str(self.eq(manager, "Equation", 2, index))
            state = int(self.eq(manager, "Status"))
            result["rows"].append(
                {
                    "index": index,
                    "text": text,
                    "status_after_text": state,
                    "global_variable": bool(
                        self.eq(manager, "GlobalVariable", 2, index)
                    ),
                    "disabled": bool(self.eq(manager, "Disabled", 2, index)),
                }
            )
        return result

    def add_equations(self, case):
        baseline.require(
            case["id"] == "D01" and case["family"] == "global_width",
            "publication probe admits the original disclosed global-width intent only",
        )
        manager = self.manager()
        before = self.publication(manager, "before_add")
        baseline.require(before["count"] == 0, "new part unexpectedly owns equations")
        rows = []
        self.rec.data["add2_publication_probe"] = {
            "input_policy": "same original index, BSTR and Solve=False; return is observed before actual publication is checked",
            "before": before,
            "calls": rows,
        }
        self.rec.flush()
        for index, text in enumerate(baseline.equation_rows(case)):
            record = {"requested_index": index, "requested_text": text, "solve": False}
            rows.append(record)
            self.rec.flush()
            record["add2_return"] = self.eq(manager, "Add2", 1, index, text, False)
            record["status_immediately_after_add2"] = int(self.eq(manager, "Status"))
            self.rec.flush()
            record["immediate_publication"] = self.publication(
                manager, "immediate_after_add"
            )
            self.rec.flush()
            record["evaluate_all_return_ungraded"] = self.eq(manager, "EvaluateAll", 1)
            record["status_immediately_after_evaluation"] = int(
                self.eq(manager, "Status")
            )
            record["evaluated_publication"] = self.publication(
                manager, "after_evaluate_all"
            )
            self.rec.flush()
            observed = record["evaluated_publication"]
            baseline.require(
                observed["count"] == index + 1,
                "same-intent Add2 did not publish the actual expected row after evaluation",
            )
            for row, wanted in zip(
                observed["rows"], baseline.equation_rows(case)[: index + 1], strict=True
            ):
                baseline.require(
                    "".join(row["text"].split()) == "".join(wanted.split())
                    and row["global_variable"] == (row["index"] == 0)
                    and not row["disabled"],
                    "same-intent Add2 published a different text, owner or disabled row",
                )
        self.rec.data["evaluate_all_return_ungraded"] = self.eq(
            manager, "EvaluateAll", 1
        )
        self.rec.flush()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--job", type=Path, required=True)
    parser.add_argument("--sha256", required=True)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("verify", "seal", "lock"):
        commands.add_parser(name)
    active = commands.add_parser("phase")
    active.add_argument("--phase", choices=baseline.PHASES, required=True)
    recovery = commands.add_parser("recover")
    recovery.add_argument("--journal", type=Path, required=True)
    recovery.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    job = baseline.read_job(args.job, args.sha256)
    baseline.require(
        job["publication_probe"]["base_protocol_sha256"]
        == "83790d7f1bf268d310f14dfdecbfc269ba804fdcaf02b3df5fadf5f6e93567a2"
        and job["publication_probe"]["only_disclosed_slot"] == "D01"
        and job["publication_probe"]["input_change_count"] == 0,
        "the narrow same-input publication probe differs",
    )
    if args.command == "verify":
        result = {
            "passed": True,
            "native_processes_started": 0,
            "sealed_inputs_read": 0,
            "files": len(job["files_sha256"]),
            "protocol_sha256": args.sha256,
        }
    elif args.command == "seal":
        result = baseline.seal_intents(args.job, args.sha256, "D01")
    elif args.command == "phase":
        baseline.EquationAuthor = PublicationAuthor
        result = baseline.phase(args.job, args.sha256, "D01", args.phase)
    elif args.command == "lock":
        result = baseline.lock_case(args.job, args.sha256, "D01")
    else:
        result = baseline.recover(args.job, args.sha256, args.journal, args.output)
    print(json.dumps(result, sort_keys=True))
    return (
        0
        if result.get(
            "passed",
            result.get("source_locked", result.get("native_processes_started") == 0),
        )
        else 2
    )


if __name__ == "__main__":
    raise SystemExit(main())
