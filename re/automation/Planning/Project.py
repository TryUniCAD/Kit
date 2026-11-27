import argparse
import json
import os
import subprocess
from pathlib import Path
from Prompt import task_prompt
from concurrent.futures import ThreadPoolExecutor, as_completed


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
              "Start date": "DATE", "Target date": "DATE", "Dependencies": "TEXT", "Schedule basis": "TEXT", "Source": "TEXT", "Dispatch": "TEXT"}
    existing = graphql(token, 'query($id:ID!){node(id:$id){... on ProjectV2{fields(first:100){nodes{... on ProjectV2Field{id name} ... on ProjectV2SingleSelectField{id name}}}}}}', {"id": state["id"]})["node"]["fields"]["nodes"]
    by_name = {field["name"]: field["id"] for field in existing if "name" in field}
    for name, kind in fields.items():
        if name not in by_name:
            by_name[name] = graphql(token, 'mutation($project:ID!,$name:String!,$kind:ProjectV2CustomFieldType!){createProjectV2Field(input:{projectId:$project,name:$name,dataType:$kind}){projectV2Field{... on ProjectV2Field{id}}}}', {"project": state["id"], "name": name, "kind": kind})["createProjectV2Field"]["projectV2Field"]["id"]
        state["Fields"][name] = by_name[name]
        state_path.write_text(json.dumps(state, indent=2) + "\n")
    for name, layout, filter_text in [("Scheduled roadmap", "ROADMAP_LAYOUT", ""), ("Current work", "TABLE_LAYOUT", '"Scope type":"Open PR"'), ("All scopes", "TABLE_LAYOUT", ""), ("Unassigned scopes", "TABLE_LAYOUT", '"Agent":"Unassigned"')]:
        if name not in state["Views"]:
            view = graphql(token, 'mutation($project:ID!,$name:String!,$layout:ProjectV2ViewLayout!){createProjectV2View(input:{projectId:$project,name:$name,layout:$layout}){projectV2View{id name}}}', {"project": state["id"], "name": name, "layout": layout})["createProjectV2View"]["projectV2View"]
            state["Views"][name] = view["id"]
            state_path.write_text(json.dumps(state, indent=2) + "\n")
            if filter_text:
                graphql(token, 'mutation($id:ID!,$filter:String!){updateProjectV2View(input:{viewId:$id,filter:$filter}){projectV2View{id}}}', {"id": view["id"], "filter": filter_text})
    config_path.write_text(json.dumps({key: value for key, value in state.items() if key not in {"Items", "Published"}}, indent=2) + "\n")
    if not args.populate:
        return
    cursor = None
    while True:
        page = graphql(token, 'query($project:ID!,$cursor:String){node(id:$project){... on ProjectV2{items(first:100,after:$cursor){nodes{id content{... on DraftIssue{body}}} pageInfo{hasNextPage endCursor}}}}}', {"project": state["id"], "cursor": cursor})["node"]["items"]
        for remote in page["nodes"]:
            body = (remote.get("content") or {}).get("body", "")
            if body.startswith("<!-- KitScope:"):
                scope = body.split(" -->", 1)[0].removeprefix("<!-- KitScope:")
                state["Items"][scope] = remote["id"]
        if not page["pageInfo"]["hasNextPage"]:
            break
        cursor = page["pageInfo"]["endCursor"]
    state_path.write_text(json.dumps(state, indent=2) + "\n")
    remaining = [item for item in board["Items"] if item["Id"] not in state.get("Published", [])]
    def publish(item):
        batch = [item]
        resolved = dict(state["Items"])
        creates = []
        variables = {"project": state["id"]}
        declarations = ["$project:ID!"]
        for index, item in enumerate(batch):
            if item["Id"] in resolved:
                continue
            variables[f"title{index}"] = item["Id"] + " · " + item["Name"]
            variables[f"body{index}"] = "<!-- KitScope:" + item["Id"] + " -->\n\nRecorded owner/contact: " + item["Owner"] + "\n\nCopy this prompt to the chosen agent. Assignment does not launch a runtime.\n\n```text\n" + task_prompt(item) + "\n```"
            declarations.extend([f"$title{index}:String!", f"$body{index}:String!"])
            creates.append(f'c{index}:addProjectV2DraftIssue(input:{{projectId:$project,title:$title{index},body:$body{index}}}){{projectItem{{id}}}}')
        if creates:
            created = graphql(token, "mutation(" + ",".join(declarations) + "){" + " ".join(creates) + "}", variables)
            for index, item in enumerate(batch):
                if f"c{index}" in created:
                    resolved[item["Id"]] = created[f"c{index}"]["projectItem"]["id"]
        mutations = []
        variables = {"project": state["id"]}
        declarations = ["$project:ID!"]
        for index, item in enumerate(batch):
            variables[f"item{index}"] = resolved[item["Id"]]
            declarations.append(f"$item{index}:ID!")
            values = {"Area": item["Area"], "Scope type": item["Kind"], "Agent": item["Owner"]}
            if item["Start"]:
                values["Start date"] = item["Start"]
                values["Target date"] = item["Finish"]
            for field_index, (name, value) in enumerate(values.items()):
                suffix = f"{index}x{field_index}"
                variables["field" + suffix] = by_name[name]
                variables["value" + suffix] = value
                declarations.extend([f"$field{suffix}:ID!", f"$value{suffix}:" + ("Date!" if fields[name] == "DATE" else "String!")])
                value_type = "date" if fields[name] == "DATE" else "text"
                mutations.append(f'v{suffix}:updateProjectV2ItemFieldValue(input:{{projectId:$project,itemId:$item{index},fieldId:$field{suffix},value:{{{value_type}:$value{suffix}}}}}){{projectV2Item{{id}}}}')
        graphql(token, "mutation(" + ",".join(declarations) + "){" + " ".join(mutations) + "}", variables)
        return item["Id"], resolved[item["Id"]]

    errors = []
    with ThreadPoolExecutor(max_workers=8) as workers:
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
