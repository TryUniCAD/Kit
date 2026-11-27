import argparse
import json
from pathlib import Path

from Lease import project_lock
from Project import graphql


def main():
    parser = argparse.ArgumentParser(description="Plan or apply verified native scope assignees without clearing existing assignments")
    parser.add_argument("--token-file", type=Path, required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    project = json.loads((root / "Documentation/Planning/Project.json").read_text())
    board = json.loads((root / "Documentation/Planning/Generated/BoardData.json").read_text())
    mappings = json.loads((root / "Documentation/Planning/AssigneeMappings.json").read_text())
    snapshot = json.loads((root / "Documentation/Planning/PullRequests.json").read_text())
    token = args.token_file.read_text().strip()
    if args.apply:
        lease = project_lock(project["id"])
    authors = {"PR" + str(item["number"]): item.get("author") for item in snapshot["PullRequests"]}
    named = {"jdharcourt", "Stephen316", "usehoplite", "odinglyn0"}
    desired = {}
    gaps = []
    for item in board["Items"]:
        if item["Status"].lower() not in {"active", "checking", "open", "complete"}:
            continue
        accounts = mappings["Explicit"].get(item["Id"], mappings["Aliases"].get(item["Owner"], []))
        basis = "explicit account mapping"
        if not accounts and item["Owner"] in named:
            accounts, basis = [item["Owner"]], "explicit owning-register account"
        if not accounts and item["Id"] in authors and authors[item["Id"]] in named:
            accounts, basis = [authors[item["Id"]]], "verified author of this exact delivery; not broader feature ownership"
        if not accounts and item["Owner"].startswith("Bounded work: "):
            accounts = [value.strip() for value in item["Owner"].removeprefix("Bounded work: ").split(",") if value.strip() in named]
            basis = "explicit bounded contribution links only"
        if not accounts:
            gaps.append(item["Id"])
            continue
        desired[item["Id"]] = {"Accounts": accounts, "Basis": basis}
    users = {}
    unavailable = {}
    for login in sorted({account for value in desired.values() for account in value["Accounts"]}):
        try:
            result = graphql(token, 'query($login:String!){user(login:$login){id login}}', {"login": login})["user"]
        except ValueError as error:
            unavailable[login] = str(error)
            continue
        if result and result["login"].casefold() == login.casefold():
            users[login] = result["id"]
    remote = {}
    cursor = None
    while True:
        page = graphql(token, 'query($project:ID!,$cursor:String){node(id:$project){... on ProjectV2{items(first:100,after:$cursor){nodes{fieldValueByName(name:"Status"){... on ProjectV2ItemFieldSingleSelectValue{name}} content{... on DraftIssue{id title assignees(first:100){nodes{id login} pageInfo{hasNextPage}}}}} pageInfo{hasNextPage endCursor}}}}}', {"project": project["id"], "cursor": cursor})["node"]["items"]
        for row in page["nodes"]:
            content = row.get("content") or {}
            scope = content.get("title", "").split(" · ", 1)[0]
            if scope in desired:
                remote.setdefault(scope, []).append({**content, "NativeStatus": (row.get("fieldValueByName") or {}).get("name")})
        if not page["pageInfo"]["hasNextPage"]:
            break
        cursor = page["pageInfo"]["endCursor"]
    report = {"Assignments": desired, "UnknownAccountMappings": gaps, "Applied": [], "Blocked": {}, "UnavailableAccounts": unavailable}
    for scope, value in desired.items():
        if scope not in remote:
            report["Blocked"][scope] = "Project scope not yet imported"
            continue
        if len(remote[scope]) != 1:
            report["Blocked"][scope] = "Duplicate scope records require reconciliation first"
            continue
        if any(account not in users for account in value["Accounts"]):
            report["Blocked"][scope] = "GitHub account could not be verified"
            continue
        content = remote[scope][0]
        if content["NativeStatus"] not in {"In Progress", "Done"}:
            report["Blocked"][scope] = "Reconcile recorded native status before assigning claimed or completed work"
            continue
        if content["assignees"]["pageInfo"]["hasNextPage"]:
            report["Blocked"][scope] = "Existing assignee pagination must be resolved before preservation"
            continue
        current = {user["id"] for user in content["assignees"]["nodes"]}
        targets = current | {users[account] for account in value["Accounts"]}
        if not args.apply or targets == current:
            continue
        try:
            updated = graphql(token, 'mutation($draft:ID!,$users:[ID!]!){updateProjectV2DraftIssue(input:{draftIssueId:$draft,assigneeIds:$users}){draftIssue{assignees(first:100){nodes{id} pageInfo{hasNextPage}}}}}', {"draft": content["id"], "users": sorted(targets)})["updateProjectV2DraftIssue"]["draftIssue"]["assignees"]
            if updated["pageInfo"]["hasNextPage"] or {user["id"] for user in updated["nodes"]} != targets:
                report["Blocked"][scope] = "Native assignment readback differs from requested preserved union"
                continue
            report["Applied"].append(scope)
        except ValueError as error:
            report["Blocked"][scope] = str(error)
    (root / "Documentation/Planning/AssignmentAudit.json").write_text(json.dumps(report, indent=2) + "\n")
    print("Verified task mappings", len(desired), "unknown mappings", len(gaps), "applied", len(report["Applied"]), "blocked", len(report["Blocked"]))


if __name__ == "__main__":
    main()
