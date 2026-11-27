import argparse
import json
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

from Lease import project_lock
from Project import graphql


REVISION = "deaf10fd15401d88c1654c75b9880ffe2743e66a"
ACCEPTED_REVISIONS = [REVISION, "8754dedca81a6a0753ddfd7081df5a9d961b2f35", "c217967da65a4c41d164dd7d133101a4b9b886b3"]
FIELDS = 'id scope:fieldValueByName(name:"Scope ID"){... on ProjectV2ItemFieldTextValue{text}} start:fieldValueByName(name:"Start date"){... on ProjectV2ItemFieldDateValue{date}} finish:fieldValueByName(name:"Target date"){... on ProjectV2ItemFieldDateValue{date}} basis:fieldValueByName(name:"Schedule basis"){... on ProjectV2ItemFieldTextValue{text}} content{... on DraftIssue{body}}'


def owned_forecast(row, old):
    scope = (row.get("scope") or {}).get("text")
    if not scope or (row.get("basis") or {}).get("text") != "Proposed investigation timebox":
        return False
    if not (row.get("content") or {}).get("body", "").startswith("<!-- KitScope:" + scope + " -->"):
        return False
    return any(
        expected.get("Start")
        and expected.get("Finish")
        and expected.get("ScheduleKind") == "Proposed investigation timebox"
        and (row.get("start") or {}).get("date") == expected["Start"]
        and (row.get("finish") or {}).get("date") == expected["Finish"]
        for expected in old.get(scope, [])
    )


def read_items(token, ids):
    return graphql(token, 'query($ids:[ID!]!){nodes(ids:$ids){... on ProjectV2Item{' + FIELDS + '}}}', {"ids": ids})["nodes"]


def clear_batch(token, project, rows, old):
    fresh = read_items(token, [row["id"] for row in rows])
    kept = [row for row in fresh if row and owned_forecast(row, old)]
    skipped = [row["id"] for row in rows if row["id"] not in {value["id"] for value in kept}]
    if not kept:
        return {"Cleared": [], "SkippedManual": skipped, "Partial": {}, "Error": None}
    variables = {"project": project["id"], "start": project["Fields"]["Start date"], "finish": project["Fields"]["Target date"]}
    declarations = ['$project:ID!', '$start:ID!', '$finish:ID!']
    mutations = []
    for index, row in enumerate(kept):
        name = "item" + str(index)
        variables[name] = row["id"]
        declarations.append('$' + name + ':ID!')
        for field in ("start", "finish"):
            mutations.append(field + str(index) + ':clearProjectV2ItemFieldValue(input:{projectId:$project,itemId:$' + name + ',fieldId:$' + field + '}){projectV2Item{id}}')
    error = None
    try:
        graphql(token, 'mutation(' + ','.join(declarations) + '){' + ' '.join(mutations) + '}', variables)
    except ValueError as problem:
        error = str(problem)
    observed = read_items(token, [row["id"] for row in kept])
    cleared = []
    partial = {}
    if {row["id"] for row in observed if row} != {row["id"] for row in kept}:
        error = (error + "; " if error else "") + "Some attempted items were unavailable during readback"
    for row in observed:
        if not row:
            continue
        empty = [field for field in ("start", "finish") if not (row.get(field) or {}).get("date")]
        if len(empty) == 2:
            cleared.append({"ItemId": row["id"], "ScopeId": row["scope"]["text"]})
        else:
            partial[row["id"]] = {"ClearedFields": empty, "ObservedStart": (row.get("start") or {}).get("date"), "ObservedFinish": (row.get("finish") or {}).get("date")}
    return {"Cleared": cleared, "SkippedManual": skipped, "Partial": partial, "Error": error}


def main():
    parser = argparse.ArgumentParser(description="Clear only unchanged task-generated forecast dates and preserve manual schedules")
    parser.add_argument("--token-file", type=Path, required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    project = json.loads((root / "Documentation/Planning/Project.json").read_text())
    lease = project_lock(project["id"])
    token = args.token_file.read_text().strip()
    old = {}
    for revision in ACCEPTED_REVISIONS:
        saved = subprocess.run(["git", "show", revision + ":Documentation/Planning/Generated/BoardData.json"], cwd=root, text=True, capture_output=True, check=True)
        for item in json.loads(saved.stdout)["Items"]:
            old.setdefault(item["Id"], []).append(item)
    rows = []
    cursor = None
    while True:
        page = graphql(token, 'query($project:ID!,$cursor:String){node(id:$project){... on ProjectV2{items(first:100,after:$cursor){nodes{' + FIELDS + '} pageInfo{hasNextPage endCursor}}}}}', {"project": project["id"], "cursor": cursor})["node"]["items"]
        rows.extend(page["nodes"])
        if not page["pageInfo"]["hasNextPage"]:
            break
        cursor = page["pageInfo"]["endCursor"]
    candidates = [row for row in rows if owned_forecast(row, old)]
    output = root / "Documentation/Planning/ForecastRemoval.json"
    previous = json.loads(output.read_text()) if output.exists() else {}
    if previous and (previous.get("SourceRevision") != REVISION or previous.get("Project") != project["url"]):
        raise ValueError("Existing forecast-removal receipt belongs to another project or source revision")
    report = {
        "ObservedAt": datetime.now(timezone.utc).isoformat(),
        "SourceRevision": REVISION,
        "AcceptedSourceRevisions": ACCEPTED_REVISIONS,
        "Project": project["url"],
        "Applied": args.apply,
        "Candidates": [{"ItemId": row["id"], "ScopeId": row["scope"]["text"]} for row in candidates],
        "SkippedManual": [row["id"] for row in rows if not owned_forecast(row, old) and ((row.get("start") or {}).get("date") or (row.get("finish") or {}).get("date"))],
        "ClearedIds": previous.get("ClearedIds", []),
        "ClearedScopes": previous.get("ClearedScopes", []),
        "PreviouslyClearedCount": len(previous.get("ClearedIds", [])),
        "Partial": {},
        "Errors": [],
        "PriorErrors": previous.get("PriorErrors", []) + ([{"ObservedAt": previous.get("ObservedAt"), "Errors": previous["Errors"]}] if previous.get("Errors") else []),
    }
    output.write_text(json.dumps(report, indent=2) + "\n")
    if args.apply:
        with ThreadPoolExecutor(max_workers=2) as pool:
            for offset in range(0, len(candidates), 10):
                futures = [pool.submit(clear_batch, token, project, candidates[start:start + 5], old) for start in range(offset, min(offset + 10, len(candidates)), 5)]
                for future in as_completed(futures):
                    try:
                        result = future.result()
                    except (ValueError, subprocess.SubprocessError) as problem:
                        report["Errors"].append(str(problem))
                    else:
                        report["ClearedIds"].extend(row["ItemId"] for row in result["Cleared"])
                        report["ClearedScopes"].extend(row["ScopeId"] for row in result["Cleared"])
                        report["SkippedManual"].extend(result["SkippedManual"])
                        report["Partial"].update(result["Partial"])
                        if result["Error"]:
                            report["Errors"].append(result["Error"])
                    output.write_text(json.dumps(report, indent=2) + "\n")
                if report["Errors"] or report["Partial"]:
                    break
    print("Eligible", len(candidates), "cleared", len(report["ClearedIds"]), "manual schedules preserved", len(report["SkippedManual"]), "errors", len(report["Errors"]), "partial", len(report["Partial"]))


if __name__ == "__main__":
    main()
