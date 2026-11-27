import argparse
import json
import os
import subprocess
from pathlib import Path
from Prompt import task_prompt
from concurrent.futures import ThreadPoolExecutor, as_completed


def rest(token, path, payload=None):
    command = ["gh", "api", path, "-H", "X-GitHub-Api-Version: 2026-03-10"]
    if payload is not None:
        command.extend(["--method", "PATCH", "--input", "-"])
    response = subprocess.run(command, input=json.dumps(payload) if payload is not None else None,
        text=True, capture_output=True, timeout=90, env={**os.environ, "GH_TOKEN": token}, check=False)
    if response.returncode:
        raise ValueError(response.stderr)
    return json.loads(response.stdout)


def graphql(token, query, variables):
    response = subprocess.run(["gh", "api", "graphql", "--input", "-"],
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
    for name, layout, filter_text in [("Scheduled roadmap", "ROADMAP_LAYOUT", ""), ("Current work", "TABLE_LAYOUT", 'scope-type:"Open PR"'), ("All scopes", "TABLE_LAYOUT", ""), ("Unassigned scopes", "TABLE_LAYOUT", 'agent:Unassigned')]:
        if name not in state["Views"]:
            view = graphql(token, 'mutation($project:ID!,$name:String!,$layout:ProjectV2ViewLayout!){createProjectV2View(input:{projectId:$project,name:$name,layout:$layout}){projectV2View{id name}}}', {"project": state["id"], "name": name, "layout": layout})["createProjectV2View"]["projectV2View"]
            state["Views"][name] = view["id"]
            state_path.write_text(json.dumps(state, indent=2) + "\n")
            if filter_text:
                graphql(token, 'mutation($id:ID!,$filter:String!){updateProjectV2View(input:{viewId:$id,filter:$filter}){projectV2View{id}}}', {"id": view["id"], "filter": filter_text})
    config_path.write_text(json.dumps({key: value for key, value in state.items() if key not in {"Items", "Published", "NumericItems"}}, indent=2) + "\n")
    if not args.populate:
        return
    cursor = None
    while True:
        page = graphql(token, 'query($project:ID!,$cursor:String){node(id:$project){... on ProjectV2{items(first:100,after:$cursor){nodes{id fullDatabaseId content{... on DraftIssue{body}}} pageInfo{hasNextPage endCursor}}}}}', {"project": state["id"], "cursor": cursor})["node"]["items"]
        for remote in page["nodes"]:
            body = (remote.get("content") or {}).get("body", "")
            if body.startswith("<!-- KitScope:"):
                scope = body.split(" -->", 1)[0].removeprefix("<!-- KitScope:")
                state["Items"][scope] = remote["id"]
                state.setdefault("NumericItems", {})[scope] = remote["fullDatabaseId"]
        if not page["pageInfo"]["hasNextPage"]:
            break
        cursor = page["pageInfo"]["endCursor"]
    state_path.write_text(json.dumps(state, indent=2) + "\n")
    remaining = [item for item in board["Items"] if item["Id"] not in state.get("Published", [])]
    numeric_fields = {field["name"]: field["id"] for field in rest(token, "/orgs/TryUniCAD/projectsV2/1/fields")}
    def publish(item):
        remote_id = state["Items"].get(item["Id"])
        if remote_id:
            numeric_id = state["NumericItems"][item["Id"]]
        else:
            body = "<!-- KitScope:" + item["Id"] + " -->\n\nRecorded owner/contact: " + item["Owner"] + "\n\nCopy this prompt to the chosen agent. Assignment does not launch a runtime.\n\n```text\n" + task_prompt(item) + "\n```"
            created = graphql(token, 'mutation($project:ID!,$title:String!,$body:String!){addProjectV2DraftIssue(input:{projectId:$project,title:$title,body:$body}){projectItem{id fullDatabaseId}}}',
                              {"project": state["id"], "title": item["Id"] + " · " + item["Name"], "body": body})["addProjectV2DraftIssue"]["projectItem"]
            remote_id, numeric_id = created["id"], created["fullDatabaseId"]
        values = {"Scope ID": item["Id"], "Agent": item["Owner"], "Area": item["Area"], "Scope type": item["Kind"],
                  "Recorded status": item["Status"], "Dependencies": ", ".join(item["Dependencies"]),
                  "Schedule basis": item.get("ScheduleKind", ""), "Source": item["Source"], "Dispatch": "Copy prompt from item body; runtime launch not configured"}
        if item["Start"]:
            values["Start date"] = item["Start"]
            values["Target date"] = item["Finish"]
        rest(token, "/orgs/TryUniCAD/projectsV2/1/items/" + str(numeric_id),
             {"fields": [{"id": numeric_fields[name], "value": value if value != "" else None} for name, value in values.items()]})
        return item["Id"], remote_id

    errors = []
    with ThreadPoolExecutor(max_workers=3) as workers:
        futures = [workers.submit(publish, item) for item in remaining]
        for future in as_completed(futures):
            try:
                scope_id, remote_id = future.result()
                state["Items"][scope_id] = remote_id
                state.setdefault("Published", []).append(scope_id)
                state_path.write_text(json.dumps(state, indent=2) + "\n")
                print(f"Published {len(state['Published'])} / {len(board['Items'])}", flush=True)
            except Exception as error:
                errors.append(str(error))
                for pending in futures:
                    pending.cancel()
    if errors:
        raise ValueError("Project population stopped; successful items retained: " + errors[0])



if __name__ == "__main__":
    main()
