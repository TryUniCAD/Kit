import argparse
import json
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from Lease import project_lock
from Project import graphql, rest
from BatchFields import load_fields
from Prompt import task_prompt


def save_state(path, state):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(state, indent=2) + "\n")
    temporary.replace(path)


def scan(token, project, state, path):
    found = {}
    cursor = None
    while True:
        page = graphql(token, 'query($project:ID!,$cursor:String){node(id:$project){... on ProjectV2{items(first:100,after:$cursor){nodes{id fullDatabaseId content{... on DraftIssue{body}} fieldValues(first:100){nodes{... on ProjectV2ItemFieldTextValue{text field{... on ProjectV2Field{name}}} ... on ProjectV2ItemFieldDateValue{date field{... on ProjectV2Field{name}}} ... on ProjectV2ItemFieldSingleSelectValue{optionId name field{... on ProjectV2SingleSelectField{name}}}}}} pageInfo{hasNextPage endCursor}}}}}', {"project": project, "cursor": cursor})["node"]["items"]
        for row in page["nodes"]:
            body = (row.get("content") or {}).get("body", "")
            if not body.startswith("<!-- KitScope:"):
                continue
            scope = body.split(" -->", 1)[0].removeprefix("<!-- KitScope:")
            if scope in found:
                state["NeedsRescan"] = True
                save_state(path, state)
                raise ValueError("Duplicate remote scope requires reconciliation before import: " + scope)
            values = {(value.get("field") or {}).get("name"): value.get("text", value.get("date", value.get("optionId"))) for value in row["fieldValues"]["nodes"]}
            status = next((value.get("name") for value in row["fieldValues"]["nodes"] if (value.get("field") or {}).get("name") == "Status"), None)
            found[scope] = {"Id": row["id"], "NumericId": row["fullDatabaseId"], "Fields": values, "Status": status}
        if not page["pageInfo"]["hasNextPage"]:
            break
        cursor = page["pageInfo"]["endCursor"]
    state["Items"] = found
    state["NeedsRescan"] = False
    save_state(path, state)


def missing_values(item, remote, status_options):
    values = {"Scope ID": item["Id"], "Agent": item["Owner"], "Area": item["Area"], "Scope type": item["Kind"], "Recorded status": item["Status"], "Dependencies": ", ".join(item["Dependencies"]), "Schedule basis": item.get("ScheduleKind", ""), "Source": item["Source"], "Dispatch": "Copy prompt from item body; runtime launch not configured"}
    if item.get("Start"):
        values.update({"Start date": item["Start"], "Target date": item["Finish"]})
    values = {name: value for name, value in values.items() if name not in remote["Fields"] or remote["Fields"][name] in {None, ""}}
    status = item["Status"].lower()
    if not remote["Status"] or remote["Status"] == "Todo" and status in {"active", "checking", "open", "complete"}:
        values["Status"] = status_options["Done" if status == "complete" else "In Progress" if status in {"active", "checking", "open"} else "Todo"]
    return {name: value for name, value in values.items() if value not in {None, ""}}


def main():
    parser = argparse.ArgumentParser(description="Resume one locked project import with batches of at most twenty draft creations")
    parser.add_argument("--token-file", type=Path, required=True)
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--only", action="append", default=[])
    parser.add_argument("--batch-size", type=int, choices=range(1, 21), default=20)
    args = parser.parse_args()
    root = args.root.resolve()
    path = args.state.resolve()
    if path == root or root in path.parents:
        raise ValueError("Transient import state must remain outside the repository")
    project = json.loads((root / "Documentation/Planning/Project.json").read_text())
    board = json.loads((root / "Documentation/Planning/Generated/BoardData.json").read_text())
    items = {item["Id"]: item for item in board["Items"]}
    if len(items) != len(board["Items"]):
        raise ValueError("Generated planning contains duplicate scope IDs")
    if args.only:
        if set(args.only) - items.keys():
            raise ValueError("Unknown explicitly selected scope")
        items = {key: value for key, value in items.items() if key in args.only}
    lease = project_lock(project["id"])
    token = args.token_file.read_text().strip()
    state = {"Project": project["id"], "Items": {}, "NeedsRescan": True}
    save_state(path, state)
    scan(token, project["id"], state, path)
    fields = load_fields(token, project)
    status_options = {option["name"]: option["id"] for option in fields["Status"]["options"]}
    numeric_fields = {field["name"]: field["id"] for field in rest(token, "/orgs/TryUniCAD/projectsV2/1/fields")}
    remaining = [item for item in items.values() if item["Id"] not in state["Items"] or missing_values(item, state["Items"][item["Id"]], status_options)]
    remaining.sort(key=lambda item: item["Status"].lower() not in {"active", "checking", "open", "complete"})
    print("Remote scopes", len(state["Items"]), "remaining", len(remaining), flush=True)
    for offset in range(0, len(remaining), args.batch_size):
        batch = remaining[offset:offset + args.batch_size]
        missing = [item for item in batch if item["Id"] not in state["Items"]]
        if missing:
            variables = {"project": project["id"]}
            declarations = ["$project:ID!"]
            mutations = []
            for index, item in enumerate(missing):
                variables["title" + str(index)] = (item["Id"] + " · " + item["Name"])[:240]
                variables["body" + str(index)] = "<!-- KitScope:" + item["Id"] + " -->\n\nRecorded owner/contact: " + item["Owner"] + "\n\nCopy this prompt to the chosen agent. Assignment does not launch a runtime.\n\n```text\n" + task_prompt(item) + "\n```"
                declarations.extend([f"$title{index}:String!", f"$body{index}:String!"])
                mutations.append(f"c{index}:addProjectV2DraftIssue(input:{{projectId:$project,title:$title{index},body:$body{index}}}){{projectItem{{id fullDatabaseId}}}}")
            state["NeedsRescan"] = True
            save_state(path, state)
            try:
                result = graphql(token, "mutation(" + ",".join(declarations) + "){" + " ".join(mutations) + "}", variables)
                for index, item in enumerate(missing):
                    row = result["c" + str(index)]["projectItem"]
                    if not row.get("id") or not row.get("fullDatabaseId"):
                        raise ValueError("Draft creation returned an incomplete item identity")
                    state["Items"][item["Id"]] = {"Id": row["id"], "NumericId": row["fullDatabaseId"], "Fields": {}, "Status": None}
                    save_state(path, state)
                state["NeedsRescan"] = False
                save_state(path, state)
            except (ValueError, KeyError, TypeError, subprocess.TimeoutExpired):
                scan(token, project["id"], state, path)
                raise ValueError("Draft creation outcome was uncertain; remote identities rescanned and saved. Restart to resume without recreating existing scopes") from None
        changes = [(item["Id"], missing_values(item, state["Items"][item["Id"]], status_options)) for item in batch]
        changes = [(scope, values) for scope, values in changes if values]
        state["NeedsRescan"] = True
        save_state(path, state)
        errors = []
        with ThreadPoolExecutor(max_workers=4) as workers:
            futures = {}
            for scope, values in changes:
                future = workers.submit(rest, token, "/orgs/TryUniCAD/projectsV2/1/items/" + str(state["Items"][scope]["NumericId"]), {"fields": [{"id": numeric_fields[name], "value": value} for name, value in values.items()]})
                futures[future] = [(scope, values)]
            try:
                for future in as_completed(futures):
                    if future.cancelled():
                        continue
                    try:
                        future.result()
                    except Exception as problem:
                        errors.append(str(problem))
                        for pending in futures:
                            pending.cancel()
                        continue
                    for scope, values in futures[future]:
                        state["Items"][scope]["Fields"].update(values)
                        if "Status" in values:
                            state["Items"][scope]["Status"] = next(name for name, option in status_options.items() if option == values["Status"])
                    save_state(path, state)
            except KeyboardInterrupt:
                for pending in futures:
                    pending.cancel()
                raise
        if errors:
            scan(token, project["id"], state, path)
            state["Errors"] = errors
            save_state(path, state)
            raise ValueError("Field publication stopped after readback: " + errors[0]) from None
        state["NeedsRescan"] = False
        save_state(path, state)
        print("Published batch", min(offset + len(batch), len(remaining)), "/", len(remaining), flush=True)
    print("All recorded scopes imported; run Audit.py and Assignments.py for fresh verification", flush=True)


if __name__ == "__main__":
    main()
