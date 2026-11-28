import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from Project import graphql


def main():
    parser = argparse.ArgumentParser(description="Read back scope coverage and native project states without changing them")
    parser.add_argument("--token-file", type=Path, required=True)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[3])
    args = parser.parse_args()
    root = args.root.resolve()
    project = json.loads((root / "Documentation/Planning/Project.json").read_text())
    board = json.loads((root / "Documentation/Planning/Generated/BoardData.json").read_text())
    token = args.token_file.read_text().strip()
    remote = {}
    cursor = None
    while True:
        page = graphql(token, 'query($project:ID!,$cursor:String){node(id:$project){... on ProjectV2{items(first:100,after:$cursor){nodes{id scopeKey:fieldValueByName(name:"Scope ID"){... on ProjectV2ItemFieldTextValue{text}} areaKey:fieldValueByName(name:"Area"){... on ProjectV2ItemFieldTextValue{text}} kindKey:fieldValueByName(name:"Scope type"){... on ProjectV2ItemFieldTextValue{text}} content{... on DraftIssue{title assignees(first:100){nodes{login}}}} fieldValueByName(name:"Status"){... on ProjectV2ItemFieldSingleSelectValue{name}}} pageInfo{hasNextPage endCursor}}}}}', {"project": project["id"], "cursor": cursor})["node"]["items"]
        for item in page["nodes"]:
            scope = (item.get("content") or {}).get("title", "").split(" · ", 1)[0]
            remote.setdefault(scope, []).append({"Id": item["id"], "Status": (item.get("fieldValueByName") or {}).get("name"), "ScopeIdField": (item.get("scopeKey") or {}).get("text"), "Area": (item.get("areaKey") or {}).get("text"), "Kind": (item.get("kindKey") or {}).get("text"), "Assignees": [user["login"] for user in (item.get("content") or {}).get("assignees", {}).get("nodes", [])]})
        if not page["pageInfo"]["hasNextPage"]:
            break
        cursor = page["pageInfo"]["endCursor"]
    expected = {item["Id"]: item for item in board["Items"]}
    report = {"ObservedAt": datetime.now(timezone.utc).isoformat(), "Project": project["url"],
              "ExpectedScopes": len(expected), "PresentScopes": len(expected.keys() & remote.keys()),
              "MissingScopes": sorted(expected.keys() - remote.keys()),
              "IncompleteMetadata": sorted(scope for scope, items in remote.items() if scope in expected and any(row["ScopeIdField"] != scope or not row["Area"] or not row["Kind"] for row in items)),
              "AssignedTodo": {scope: items for scope, items in remote.items() if any(row["Assignees"] and row["Status"] not in {"In Progress", "Done"} for row in items)},
              "DuplicateScopes": {scope: items for scope, items in remote.items() if scope in expected and len(items) > 1},
              "NativeStatusCounts": dict(Counter(item["Status"] or "Unset" for scope, items in remote.items() if scope in expected for item in items)),
              "RecordedDoneNotMarked": [scope for scope, item in expected.items() if item["Status"].lower() == "complete" and not any(row["Status"] == "Done" for row in remote.get(scope, []))],
              "RecordedActiveNotMarked": [scope for scope, item in expected.items() if item["Status"].lower() in {"active", "checking", "open"} and not any(row["Status"] in {"In Progress", "Done"} for row in remote.get(scope, []))]}
    (root / "Documentation/Planning/ProjectSnapshot.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: value for key, value in report.items() if key not in {"MissingScopes", "DuplicateScopes", "RecordedDoneNotMarked", "RecordedActiveNotMarked", "AssignedTodo", "IncompleteMetadata"}}))
    print("Duplicates", len(report["DuplicateScopes"]), "done mismatches", len(report["RecordedDoneNotMarked"]), "active mismatches", len(report["RecordedActiveNotMarked"]), "assigned todo", len(report["AssignedTodo"]))


if __name__ == "__main__":
    main()
