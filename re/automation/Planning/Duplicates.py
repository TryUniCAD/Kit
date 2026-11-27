import argparse
import json
import subprocess
from pathlib import Path

from Lease import project_lock
from Project import graphql, rest
from Prompt import task_prompt


def normal_body(body):
    for line in (
        "Set native project Status to In Progress before starting; set Done only with exact exit evidence.\n",
        "Do not restart completed scopes; claim an explicit follow-up child when needed.\n",
    ):
        body = body.replace(line, "")
    return body.replace("read CadSuccessCriteria.md", "read Documentation/Reference/Operations/CadSuccessCriteria.md")


def main():
    parser = argparse.ArgumentParser(description="Reconcile only equivalent task-owned duplicate scope drafts")
    parser.add_argument("--token-file", type=Path, required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    project = json.loads((root / "Documentation/Planning/Project.json").read_text())
    lease = project_lock(project["id"])
    audit = json.loads((root / "Documentation/Planning/ProjectSnapshot.json").read_text())
    token = args.token_file.read_text().strip()
    known = {}
    datasets = [json.loads((root / "Documentation/Planning/Generated/BoardData.json").read_text())]
    for revision in ("8754dedca81a6a0753ddfd7081df5a9d961b2f35", "c217967da65a4c41d164dd7d133101a4b9b886b3"):
        result = subprocess.run(["git", "show", revision + ":Documentation/Planning/Generated/BoardData.json"], cwd=root, capture_output=True, text=True, check=False)
        if result.returncode == 0:
            datasets.append(json.loads(result.stdout))
    for dataset in datasets:
        for item in dataset["Items"]:
            known.setdefault(item["Id"], []).append(item)
    for scope, candidates in known.items():
        if scope.startswith("fusion:api:"):
            for candidate in list(candidates):
                if "API type declarations" in candidate["Name"]:
                    candidates.append({**candidate, "Name": candidate["Name"].replace("API type declarations", "API feature declarations"), "Kind": "Decoding scope"})
    ids = [row["Id"] for rows in audit["DuplicateScopes"].values() for row in rows]
    records = {}
    for offset in range(0, len(ids), 30):
        result = graphql(token, 'query($ids:[ID!]!){nodes(ids:$ids){... on ProjectV2Item{id fullDatabaseId content{... on DraftIssue{id body title assignees(first:100){nodes{id login} pageInfo{hasNextPage}}}} fieldValues(first:100){nodes{... on ProjectV2ItemFieldTextValue{text field{... on ProjectV2Field{name databaseId}}} ... on ProjectV2ItemFieldDateValue{date field{... on ProjectV2Field{name databaseId}}} ... on ProjectV2ItemFieldSingleSelectValue{optionId name field{... on ProjectV2SingleSelectField{name databaseId}}}}}}}}', {"ids": ids[offset:offset + 30]})
        records.update({item["id"]: item for item in result["nodes"] if item})
    report = {"EquivalentGroups": [], "Conflicts": {}, "AssignmentDifferences": {}, "RemovedIds": []}
    for scope, listed in audit["DuplicateScopes"].items():
        rows = [records[row["Id"]] for row in listed if row["Id"] in records]
        if len(rows) < 2:
            continue
        assignments = [row["content"]["assignees"] for row in rows]
        if any(value["pageInfo"]["hasNextPage"] for value in assignments):
            report["Conflicts"][scope] = "Assignee list exceeds fetched page; retained without deleting assignments"
            continue
        assignees = {user["id"]: user["login"] for value in assignments for user in value["nodes"]}
        assigned_sets = {frozenset(user["id"] for user in value["nodes"]) for value in assignments if value["nodes"]}
        if len(assigned_sets) > 1:
            report["AssignmentDifferences"][scope] = {
                "Records": [{"Id": row["id"], "Assignees": sorted(user["login"] for user in row["content"]["assignees"]["nodes"])} for row in rows],
                "PreservedUnion": sorted(assignees.values()),
                "Disposition": "All accounts retained; coordinate responsibility explicitly",
            }
        expected_bodies = set()
        for item in known.get(scope, []):
            expected_bodies.add(normal_body("<!-- KitScope:" + scope + " -->\n\nRecorded owner/contact: " + item["Owner"] + "\n\nCopy this prompt to the chosen agent. Assignment does not launch a runtime.\n\n```text\n" + task_prompt(item) + "\n```"))
            expected_bodies.add(f'<!-- KitScope:{scope} -->\n\nScope: {scope}\n\nOwning source: {item["Source"]}\n\nRecorded owner/contact: {item["Owner"]}\n\nPrerequisites: {", ".join(item["Dependencies"]) or "Inspect source; no parent edges recorded"}\n\nExit condition:\n{json.dumps(item["Exit"], ensure_ascii=False)}\n\nSchedule is a proposed investigation window, not a feature completion promise. Read AGENTS.md and Documentation/Planning/README.md before claiming. Refresh live ownership and source prerequisites. Copy the scope prompt from the repo planning board. Assignment does not launch an agent. Do not start work already claimed by another owner.')
        bodies = {normal_body((row.get("content") or {}).get("body", "")) for row in rows}
        equivalent = bodies <= expected_bodies
        if (len(bodies) != 1 and not equivalent) or not next(iter(bodies)).startswith("<!-- KitScope:" + scope + " -->"):
            report["Conflicts"][scope] = "Distinct body content; retained for explicit reconciliation"
            continue
        merged = {}
        conflict = False
        for row in rows:
            for value in row["fieldValues"]["nodes"]:
                field = value.get("field") or {}
                if field.get("name") not in {*project["Fields"], "Status"}:
                    continue
                current = value.get("text", value.get("date", value.get("optionId")))
                if current is None:
                    continue
                prior = merged.get(field["name"])
                if prior and prior["value"] != current:
                    if field["name"] != "Status":
                        fields = {"Agent": "Owner", "Start date": "Start", "Target date": "Finish", "Scope type": "Kind", "Recorded status": "Status", "Schedule basis": "ScheduleKind", "Source": "Source"}
                        allowed = {candidate.get(fields[field["name"]]) for candidate in known.get(scope, [])} if field["name"] in fields else set()
                        if field["name"] == "Dispatch":
                            allowed = {"Copy prompt; runtime launch not configured", "Copy prompt from item body; runtime launch not configured"}
                        if prior["value"] not in allowed or current not in allowed:
                            conflict = True
                            break
                    rank = {"Todo": 0, "In Progress": 1, "Done": 2}
                    if rank.get(prior.get("state"), -1) > rank.get(value.get("name"), -1):
                        continue
                merged[field["name"]] = {"id": field["databaseId"], "value": current, "state": value.get("name")}
        if conflict:
            report["Conflicts"][scope] = "Conflicting nonempty field values; retained"
            continue
        report["EquivalentGroups"].append(scope)
        if not args.apply:
            continue
        canonical = rows[0]
        current = known[scope][0]
        body = "<!-- KitScope:" + scope + " -->\n\nRecorded owner/contact: " + current["Owner"] + "\n\nCopy this prompt to the chosen agent. Assignment does not launch a runtime.\n\n```text\n" + task_prompt(current) + "\n```"
        saved = graphql(token, 'mutation($draft:ID!,$body:String!,$title:String!,$assignees:[ID!]!){updateProjectV2DraftIssue(input:{draftIssueId:$draft,body:$body,title:$title,assigneeIds:$assignees}){draftIssue{id assignees(first:100){nodes{id} pageInfo{hasNextPage}}}}}', {"draft": canonical["content"]["id"], "body": body, "title": (scope + " · " + current["Name"])[:240], "assignees": sorted(assignees)})["updateProjectV2DraftIssue"]["draftIssue"]["assignees"]
        if saved["pageInfo"]["hasNextPage"] or {user["id"] for user in saved["nodes"]} != set(assignees):
            raise ValueError("Canonical assignees were not preserved for " + scope + "; duplicates retained")
        rest(token, "/orgs/TryUniCAD/projectsV2/1/items/" + str(canonical["fullDatabaseId"]), {"fields": [{"id": value["id"], "value": value["value"]} for value in merged.values()]})
        for duplicate in rows[1:]:
            graphql(token, 'mutation($project:ID!,$item:ID!){deleteProjectV2Item(input:{projectId:$project,itemId:$item}){deletedItemId}}', {"project": project["id"], "item": duplicate["id"]})
            report["RemovedIds"].append(duplicate["id"])
    (root / "Documentation/Planning/DuplicateReconciliation.json").write_text(json.dumps(report, indent=2) + "\n")
    print("Equivalent groups", len(report["EquivalentGroups"]), "conflicts retained", len(report["Conflicts"]), "assignment differences", len(report["AssignmentDifferences"]), "removed", len(report["RemovedIds"]))


if __name__ == "__main__":
    main()
