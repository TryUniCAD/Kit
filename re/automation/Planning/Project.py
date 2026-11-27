import argparse
import json
import os
import subprocess
from pathlib import Path
from Prompt import task_prompt
from concurrent.futures import ThreadPoolExecutor, as_completed
from Lease import project_lock


def rest(token, path, payload=None, method="PATCH"):
    if not token or len(token) > 4096 or any(value.isspace() for value in token):
        raise ValueError("A nonempty single-line project credential is required")
    command = ["gh", "api", "--hostname", "github.com", path, "-H", "X-GitHub-Api-Version: 2026-03-10"]
    if payload is not None:
        command.extend(["--method", method, "--input", "-"])
    response = subprocess.run(command, input=json.dumps(payload) if payload is not None else None,
        text=True, capture_output=True, timeout=90, env={**os.environ, "GH_TOKEN": token}, check=False)
    if response.returncode:
        raise ValueError(response.stderr)
    return json.loads(response.stdout)


def graphql(token, query, variables):
    if not token or len(token) > 4096 or any(value.isspace() for value in token):
        raise ValueError("A nonempty single-line project credential is required")
    response = subprocess.run(["gh", "api", "--hostname", "github.com", "graphql", "--input", "-"],
        input=json.dumps({"query": query, "variables": variables}), text=True,
        capture_output=True, timeout=90, env={**os.environ, "GH_TOKEN": token}, check=False)
    if response.returncode:
        raise ValueError(response.stderr)
    result = json.loads(response.stdout)
    if result.get("errors"):
        raise ValueError(json.dumps(result["errors"]))
    return result["data"]


def main():
    parser = argparse.ArgumentParser(description="Provision and populate the authorized organization planning project")
    parser.add_argument("--token-file", type=Path, required=True)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--populate", action="store_true")
    parser.add_argument("--status-only", action="store_true")
    parser.add_argument("--owner-id", required=True)
    parser.add_argument("--state", type=Path, required=True)
    args = parser.parse_args()
    token = args.token_file.read_text().strip()
    root = args.root.resolve()
    config_path = root / "Documentation/Planning/Project.json"
    state_path = args.state
    board = json.loads((root / "Documentation/Planning/Generated/BoardData.json").read_text())
    if state_path.exists():
        state = json.loads(state_path.read_text())
    elif config_path.exists():
        state = json.loads(config_path.read_text())
        state.update(Items={}, Published=[])
    else:
        owner = graphql(token, 'query { viewer { login } }', {})
        project = graphql(token, 'mutation($owner:ID!){createProjectV2(input:{ownerId:$owner,title:"Kit development and decoding"}){projectV2{id number url}}}', {"owner": args.owner_id})["createProjectV2"]["projectV2"]
        state = {**project, "Repository": "TryUniCAD/Kit", "CreatedBy": owner["viewer"]["login"], "Fields": {}, "Views": {}, "Items": {}}
        state_path.write_text(json.dumps(state, indent=2) + "\n")
        print(project["url"], flush=True)
    lease = project_lock(state["id"])
    fields = {"Scope ID": "TEXT", "Agent": "TEXT", "Area": "TEXT", "Scope type": "TEXT", "Recorded status": "TEXT",
              "Start date": "DATE", "Target date": "DATE", "Dependencies": "TEXT", "Schedule basis": "TEXT", "Source": "TEXT", "Dispatch": "TEXT", "Runner": "SINGLE_SELECT"}
    existing = graphql(token, 'query($id:ID!){node(id:$id){... on ProjectV2{fields(first:100){nodes{... on ProjectV2Field{id name} ... on ProjectV2SingleSelectField{id name}}}}}}', {"id": state["id"]})["node"]["fields"]["nodes"]
    by_name = {field["name"]: field["id"] for field in existing if "name" in field}
    for name, kind in fields.items():
        if name not in by_name:
            if kind == "SINGLE_SELECT":
                by_name[name] = graphql(token, 'mutation($project:ID!,$name:String!){createProjectV2Field(input:{projectId:$project,name:$name,dataType:SINGLE_SELECT,singleSelectOptions:[{name:"Unassigned",color:GRAY,description:"No runtime selected"},{name:"Local Codex",color:GREEN,description:"Local agent handoff"},{name:"Hoplite",color:ORANGE,description:"Hoplite handoff"},{name:"GitHub coding agent",color:PURPLE,description:"Configured GitHub agent integration"}]}){projectV2Field{... on ProjectV2SingleSelectField{id}}}}', {"project": state["id"], "name": name})["createProjectV2Field"]["projectV2Field"]["id"]
            else:
                by_name[name] = graphql(token, 'mutation($project:ID!,$name:String!,$kind:ProjectV2CustomFieldType!){createProjectV2Field(input:{projectId:$project,name:$name,dataType:$kind}){projectV2Field{... on ProjectV2Field{id}}}}', {"project": state["id"], "name": name, "kind": kind})["createProjectV2Field"]["projectV2Field"]["id"]
        state["Fields"][name] = by_name[name]
        state_path.write_text(json.dumps(state, indent=2) + "\n")
    for name, layout, filter_text in [("Scheduled roadmap", "ROADMAP_LAYOUT", ""), ("Current work", "TABLE_LAYOUT", 'status:"In Progress"'), ("All scopes", "TABLE_LAYOUT", ""), ("Unassigned scopes", "TABLE_LAYOUT", 'agent:Unassigned')]:
        if name not in state["Views"]:
            view = graphql(token, 'mutation($project:ID!,$name:String!,$layout:ProjectV2ViewLayout!){createProjectV2View(input:{projectId:$project,name:$name,layout:$layout}){projectV2View{id name}}}', {"project": state["id"], "name": name, "layout": layout})["createProjectV2View"]["projectV2View"]
            state["Views"][name] = view["id"]
            state_path.write_text(json.dumps(state, indent=2) + "\n")
        if filter_text:
            graphql(token, 'mutation($id:ID!,$filter:String!){updateProjectV2View(input:{viewId:$id,filter:$filter}){projectV2View{id}}}', {"id": state["Views"][name], "filter": filter_text})
    config_path.write_text(json.dumps({key: value for key, value in state.items() if key in {"id", "number", "url", "Repository", "CreatedBy", "Fields", "Views"}}, indent=2) + "\n")
    if not args.populate and not args.status_only:
        return
    cursor = None
    while True:
        page = graphql(token, 'query($project:ID!,$cursor:String){node(id:$project){... on ProjectV2{items(first:100,after:$cursor){nodes{id fullDatabaseId fieldValueByName(name:"Status"){... on ProjectV2ItemFieldSingleSelectValue{name}} fieldValues(first:100){nodes{... on ProjectV2ItemFieldTextValue{text field{... on ProjectV2Field{name}}} ... on ProjectV2ItemFieldDateValue{date field{... on ProjectV2Field{name}}} ... on ProjectV2ItemFieldSingleSelectValue{optionId field{... on ProjectV2SingleSelectField{name}}}}} content{... on DraftIssue{body}}} pageInfo{hasNextPage endCursor}}}}}', {"project": state["id"], "cursor": cursor})["node"]["items"]
        for remote in page["nodes"]:
            body = (remote.get("content") or {}).get("body", "")
            if body.startswith("<!-- KitScope:"):
                scope = body.split(" -->", 1)[0].removeprefix("<!-- KitScope:")
                state["Items"][scope] = remote["id"]
                state.setdefault("NumericItems", {})[scope] = remote["fullDatabaseId"]
                state.setdefault("NativeStatus", {})[scope] = (remote.get("fieldValueByName") or {}).get("name")
                current_fields = {(value.get("field") or {}).get("name"): value.get("text", value.get("date", value.get("optionId"))) for value in remote.get("fieldValues", {}).get("nodes", [])}
                state.setdefault("RemoteFields", {})[scope] = current_fields
                if current_fields.get("Scope ID") == scope and scope not in state.setdefault("Published", []):
                    state["Published"].append(scope)
        if not page["pageInfo"]["hasNextPage"]:
            break
        cursor = page["pageInfo"]["endCursor"]
    state_path.write_text(json.dumps(state, indent=2) + "\n")
    remaining = [item for item in board["Items"] if (item["Id"] in state["Items"] if args.status_only else item["Id"] not in state.get("Published", []))]
    remaining.sort(key=lambda item: 0 if item["Status"].lower() in {"active", "checking", "open", "complete"} else 1 if item["Kind"] != "Decoding scope" else 2)
    remote_fields = rest(token, "/orgs/TryUniCAD/projectsV2/1/fields")
    numeric_fields = {field["name"]: field["id"] for field in remote_fields}
    status_options = {option["name"]["raw"]: option["id"] for field in remote_fields if field["name"] == "Status" for option in field["options"]}
    def publish(item):
        remote_id = state["Items"].get(item["Id"])
        if remote_id:
            numeric_id = state["NumericItems"][item["Id"]]
        else:
            body = "<!-- KitScope:" + item["Id"] + " -->\n\nRecorded owner/contact: " + item["Owner"] + "\n\nCopy this prompt to the chosen agent. Assignment does not launch a runtime.\n\n```text\n" + task_prompt(item) + "\n```"
            created = rest(token, "/orgs/TryUniCAD/projectsV2/1/drafts", {"title": (item["Id"] + " · " + item["Name"])[:240], "body": body}, method="POST")
            remote_id, numeric_id = created["node_id"], created["id"]
        values = {"Scope ID": item["Id"], "Agent": item["Owner"], "Area": item["Area"], "Scope type": item["Kind"],
                  "Recorded status": item["Status"], "Dependencies": ", ".join(item["Dependencies"]),
                  "Schedule basis": item.get("ScheduleKind", ""), "Source": item["Source"], "Dispatch": "Copy prompt from item body; runtime launch not configured"}
        if item["Start"]:
            values["Start date"] = item["Start"]
            values["Target date"] = item["Finish"]
        if args.status_only:
            values = {}
        else:
            existing = state.get("RemoteFields", {}).get(item["Id"], {})
            values = {name: value for name, value in values.items() if name not in existing}
        if not state.get("NativeStatus", {}).get(item["Id"]) or (state.get("NativeStatus", {}).get(item["Id"]) == "Todo" and item["Status"].lower() in {"complete", "active", "checking", "open"}):
            native_status = "Done" if item["Status"].lower() == "complete" else "In Progress" if item["Status"].lower() in {"active", "checking", "open"} else "Todo"
            values["Status"] = status_options[native_status]
        if not values:
            return item["Id"], remote_id
        rest(token, "/orgs/TryUniCAD/projectsV2/1/items/" + str(numeric_id),
             {"fields": [{"id": numeric_fields[name], "value": value if value != "" else None} for name, value in values.items()]})
        return item["Id"], remote_id

    errors = []
    with ThreadPoolExecutor(max_workers=4) as workers:
        futures = {workers.submit(publish, item): item["Id"] for item in remaining}
        try:
            for future in as_completed(futures):
                if future.cancelled():
                    continue
                try:
                    scope_id, remote_id = future.result()
                    state["Items"][scope_id] = remote_id
                    if scope_id not in state.setdefault("Published", []):
                        state["Published"].append(scope_id)
                    state_path.write_text(json.dumps(state, indent=2) + "\n")
                    print(f"Published {len(state['Published'])} / {len(board['Items'])}", flush=True)
                except Exception as error:
                    errors.append(futures[future] + ": " + str(error))
                    for pending in futures:
                        pending.cancel()
        except KeyboardInterrupt:
            for pending in futures:
                pending.cancel()
            raise

    if errors:
        raise ValueError("Project population stopped; successful items retained: " + errors[0])



if __name__ == "__main__":
    main()
