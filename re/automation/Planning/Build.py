import argparse
import hashlib
import html
import json
import re
import sqlite3
from datetime import date
from pathlib import Path
from Schedule import build_schedule, identify_rows
from Calendar import calendar_svg
from Claims import read_claims


def read_tables(root, relative):
    rows = []
    headers = []
    section = ""
    for number, line in enumerate((root / relative).read_text().splitlines(), 1):
        if line.startswith("#"):
            section = line.lstrip("# ")
        if not line.startswith("|"):
            headers = []
            continue
        cells = [cell.strip() for cell in line.strip("| ").split("|")]
        if cells[0] in {"ID", "Child ID"}:
            headers = cells
            continue
        if not headers or len(cells) != len(headers) or not re.fullmatch(r"[AB]\d\d[a-z]?(?:-[A-Za-z0-9]+)?", cells[0]):
            continue
        row = dict(zip(["ID" if cell == "Child ID" else cell for cell in headers], cells))
        rows.append({"Id": cells[0], "Section": section, "Source": relative,
                     "Line": number, "Fields": row})
    return rows


def load_scopes(root):
    relative = "re/solidworks/PlannerCatalog/Sources/FeaturePlan.json"
    plan = json.loads((root / relative).read_text())
    scopes = []
    for family in plan["families"]:
        for feature in family["subfeatures"]:
            scopes.append({"Id": "sw:" + feature["id"], "FamilyId": "sw:" + family["id"],
                           "Family": family["name"], "Name": feature["name"], "Format": "SOLIDWORKS",
                           "Wave": family["wave"], "Source": relative,
                           "FamilyDependencies": family["dependencies"], "Definition": feature})
    relative = "re/Fusion/PlannerCatalog/Data/Catalog.sqlite"
    with sqlite3.connect((root / relative).resolve().as_uri() + "?mode=ro", uri=True) as database:
        database.row_factory = sqlite3.Row
        feature_ids = {row[0] for row in database.execute("SELECT id FROM api_feature_types")}
        for row in database.execute("SELECT * FROM items WHERE kind = 'api_type' ORDER BY id"):
            scopes.append({"Id": "fusion:" + row["id"], "FamilyId": "fusion:api-features",
                           "Family": "API type declarations", "Name": row["name"], "Format": "Fusion",
                           "Wave": "unmapped", "Source": relative, "FamilyDependencies": [],
                           "ScheduleEligible": row["id"] in feature_ids,
                           "Definition": dict(row)})
        native_inventory = [dict(row) for row in database.execute("SELECT * FROM items WHERE kind IN ('native_type','native_schema','native_member','ui_command') ORDER BY id")]
    for row in native_inventory:
        if row["kind"] == "native_type":
            scopes.append({"Id": "fusion:" + row["id"], "FamilyId": "fusion:native-types", "Family": "Native decoding domains", "Name": row["name"], "Format": "Fusion", "Wave": "unmapped", "Source": relative, "FamilyDependencies": [], "ScheduleEligible": False,
                           "Definition": {**row, "Schemas": [value for value in native_inventory if value["kind"] == "native_schema" and value.get("parent_id") == row["id"]]}})
    return scopes, native_inventory


def build_tasks(rows, links):
    tasks = []
    for row in rows:
        if row["Id"] not in links["Dependencies"]:
            continue
        fields = row["Fields"]
        tasks.append({"Id": row["Id"], "Name": fields["Deliverable"],
                      "Status": fields["Status"].lower(),
                      "Owner": fields.get("Owner", fields.get("Owner and delivery", "Unassigned")),
                      "Dependencies": links["Dependencies"][row["Id"]],
                      "Area": "SDK" if row["Id"] in {"A04", "A05", "A11", "A12", "A13", "A14", "B02", "B03", "B04", "B05", "B06", "B07", "B08", "B09", "B12"} else "Project",
                      "Source": row["Source"], "Line": row["Line"],
                      "Exit": fields.get("Exit criterion", fields.get("Exit condition", "")),
                      "SourceDependencies": fields.get("Depends on", "")})
    tasks.extend(links["ExtraTasks"])
    if len({task["Id"] for task in tasks}) != len(tasks):
        raise ValueError("Duplicate parent task IDs")
    return tasks


def validate(tasks, scopes, links, snapshot, rows, claims, sdk_tasks):
    index = {task["Id"]: task for task in tasks}
    levels = {}
    visiting = set()

    def level(task_id):
        if task_id in visiting:
            raise ValueError("Dependency cycle at " + task_id)
        if task_id not in index:
            raise ValueError("Unknown dependency " + task_id)
        if task_id not in levels:
            visiting.add(task_id)
            levels[task_id] = max((level(item) + 1 for item in index[task_id]["Dependencies"]), default=0)
            visiting.remove(task_id)
        return levels[task_id]

    for task in tasks:
        level(task["Id"])
        if task["Status"] == "complete" and task in links["ExtraTasks"]:
            if not task.get("Evidence") or not re.fullmatch(r"[0-9a-f]{40}", task.get("AcceptedRevision", "")):
                raise ValueError("Completion requires evidence and accepted revision")
    scope_ids = {scope["Id"] for scope in scopes}
    linked = set()
    for claim in links["ScopeLinks"]:
        if claim["ScopeId"] not in scope_ids or claim["TaskId"] not in set(index) | {row["Id"] for row in rows} | {"PR" + str(item["number"]) for item in snapshot["PullRequests"]} | {task["Id"] for task in sdk_tasks}:
            raise ValueError("Unknown scope or task in scope link")
        if (claim["ScopeId"], claim["TaskId"]) in linked:
            raise ValueError("Duplicate scope link")
        linked.add((claim["ScopeId"], claim["TaskId"]))
        for stage, result in claim["Stages"].items():
            if stage not in {"capture", "decode", "semantics", "write", "native"}:
                raise ValueError("Unknown qualification stage")
            if result["Status"] not in {"unverified", "active", "blocked", "checking", "complete"}:
                raise ValueError("Unknown stage status")
            if result["Status"] == "complete" and (not result["Evidence"] or not re.fullmatch(r"[0-9a-f]{40}", result["Revision"])):
                raise ValueError("Stage completion requires evidence and revision")
    scheduled = set()
    all_ids = set(index) | scope_ids | {row["ScopeId"] for row in rows} | {claim["Id"] for claim in claims} | {task["Id"] for task in sdk_tasks}
    for schedule in links["Schedules"]:
        if schedule["TaskId"] not in all_ids or schedule["TaskId"] in scheduled:
            raise ValueError("Unknown or duplicate scheduled task")
        scheduled.add(schedule["TaskId"])
        if date.fromisoformat(schedule["Finish"]) < date.fromisoformat(schedule["Start"]) or not schedule["Basis"]:
            raise ValueError("Invalid schedule or missing estimate basis")
    date.fromisoformat(snapshot["ObservedOn"])
    return levels


def markdown_text(value):
    return str(value).replace("|", "\\|").replace("\n", " ")


def make_svg(tasks, levels):
    width = 1200
    height = 95 + len(tasks) * 36
    colors = {"complete": "#526d50", "blocked": "#8b554e", "active": "#9b773f", "checking": "#9b773f"}
    result = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title description">',
              '<title id="title">Kit dependency Gantt</title>',
              '<desc id="description">Ordinal dependency tiers, not elapsed time or promised delivery dates. Every bar is one task, not a duration. Status and ownership are dated register observations.</desc>',
              f'<rect width="{width}" height="{height}" fill="#faf9f6"/>',
              '<g font-family="sans-serif" font-size="12" fill="#242321">',
              '<text x="16" y="24" font-size="17">Dependency Gantt — no calendar estimates assigned</text>',
              '<text x="16" y="45">Register observations; source gates and evidence still apply · red blocked · ochre active/checking · green recorded complete</text>']
    count = max(levels.values()) + 1
    cell = 560 / count
    for tier in range(count):
        x = 610 + tier * cell
        result.extend([f'<text x="{x:.1f}" y="70">Tier {tier}</text>',
                       f'<path d="M{x:.1f} 80V{height}" stroke="#dedbd5"/>'])
    for number, task in enumerate(tasks):
        y = 100 + number * 36
        label = task["Id"] + " · " + task["Name"]
        if len(label) > 78:
            label = label[:75] + "…"
        result.extend([f'<text x="16" y="{y}">{html.escape(label)}</text>',
                       f'<text x="16" y="{y+14}" fill="#66615b" font-size="10">{html.escape(task["Status"] + " · " + task["Owner"][:95])}</text>',
                       f'<rect x="{610 + levels[task["Id"]]*cell:.1f}" y="{y-11}" width="{max(8,cell-8):.1f}" height="22" rx="2" fill="{colors.get(task["Status"], "#77716a")}"><title>{html.escape(task["Id"] + ": " + task["Exit"])}</title></rect>'])
    result.append('</g></svg>')
    return "\n".join(result) + "\n"


def make_outputs(root):
    source = root / "Documentation/Planning"
    links = json.loads((source / "Links.json").read_text())
    snapshot = json.loads((source / "PullRequests.json").read_text())
    rows = read_tables(root, "Documentation/Maintenance/ConversionBacklog.md") + read_tables(root, "Documentation/Reference/Research/AutomationSteps.md")
    rows = identify_rows(rows, json.loads((source / "TaskIdentities.json").read_text()))
    sdk_tasks = json.loads((source / "SdkScopes.json").read_text())["Tasks"]
    claims = read_claims(root, "Documentation/Maintenance/ConversionBacklog.md") + read_claims(root, "Documentation/Reference/Research/AutomationSteps.md")
    tasks = build_tasks(rows, links)
    scopes, native_inventory = load_scopes(root)
    levels = validate(tasks, scopes, links, snapshot, rows, claims, sdk_tasks)
    for scope in scopes:
        scope["TaskLinks"] = [claim for claim in links["ScopeLinks"] if claim["ScopeId"] == scope["Id"]]
    sources = ["Documentation/Planning/Links.json", "Documentation/Planning/PullRequests.json", "Documentation/Planning/SdkScopes.json", "Documentation/Planning/TaskIdentities.json",
               "Documentation/Maintenance/ConversionBacklog.md", "Documentation/Reference/Research/AutomationSteps.md",
               "re/solidworks/PlannerCatalog/Sources/FeaturePlan.json", "re/Fusion/PlannerCatalog/Data/Catalog.sqlite",
               "re/automation/Planning/Board/Board.jsx", "re/automation/Planning/Board/Board.css"]
    bundle = json.loads((source / "BundleManifest.json").read_text())
    for path, digest in bundle.items():
        if hashlib.sha256((root / path).read_bytes()).hexdigest() != digest:
            raise ValueError("Rebuild stale board asset: " + path)
    sources.extend(["Documentation/Planning/BundleManifest.json", *bundle])
    provenance = {path: hashlib.sha256((root / path).read_bytes()).hexdigest() for path in sources}
    outputs = {"Manifest.json": json.dumps({"MainRevision": links["MainRevision"], "ObservedOn": links["ObservedOn"],
               "SourceHashes": provenance, "ParentTasks": len(tasks), "RegisterRows": len(rows),
               "Scopes": len(scopes), "OpenPullRequests": sum(item.get("state", "open") == "open" for item in snapshot["PullRequests"]), "DeliveryRecords": len(snapshot["PullRequests"]), "ProseClaims": len(claims)}, indent=2) + "\n"}
    outputs["Tasks.jsonl"] = "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows)
    outputs["Claims.jsonl"] = "".join(json.dumps(claim, sort_keys=True) + "\n" for claim in claims)
    outputs["StatusAudit.json"] = json.dumps({"RecordedCompleteTasks": [row["Id"] for row in rows if row["Fields"].get("Status", "").lower() == "complete"], "RecordedActiveTasks": [row["Id"] for row in rows if row["Fields"].get("Status", "").lower() in {"active", "checking"}], "OpenDeliveryPRs": [item["number"] for item in snapshot["PullRequests"] if item.get("state", "open").lower() == "open"], "ExplicitActiveScopeLinks": links["ScopeLinks"], "Policy": "Historical task states and bounded active contributions are distinct from full feature qualification"}, indent=2) + "\n"
    outputs["NativeInventory.jsonl"] = "".join(json.dumps(row, sort_keys=True) + "\n" for row in native_inventory)
    outputs["Coverage.json"] = json.dumps({"SolidworksFamilies": len({scope["FamilyId"] for scope in scopes if scope["Format"] == "SOLIDWORKS"}), "SolidworksSubfeatures": sum(scope["Format"] == "SOLIDWORKS" for scope in scopes), "FusionApiTypes": sum(scope["Definition"].get("kind") == "api_type" for scope in scopes), "FusionNativeTypes": sum(scope["Definition"].get("kind") == "native_type" for scope in scopes), "NativeInventory": {kind: sum(row["kind"] == kind for row in native_inventory) for kind in sorted({row["kind"] for row in native_inventory})}, "UniversalVendorCoverage": "unverified; catalogues do not prove every product version or legal feature combination"}, indent=2) + "\n"
    outputs["Scopes.jsonl"] = "".join(json.dumps(scope, sort_keys=True) + "\n" for scope in scopes)
    table = ["# Task index", "", "Generated from owning registers; recorded status can be stale. Refresh linked PRs before claiming work.", "", "| Task | Scope | Recorded status | Owner/contact | Prerequisites | Exit and source |", "| --- | --- | --- | --- | --- | --- |"]
    for task in tasks:
        table.append("| " + " | ".join(markdown_text(value) for value in [task["Id"], task["Name"], task["Status"], task["Owner"], ", ".join(task["Dependencies"]) + "; " + task.get("SourceDependencies", "See source"), task["Exit"] + f' ([source](../../../{task["Source"]}))']) + " |")
    table.extend(["", "## Detailed research rows", "", "These rows preserve source dependencies verbatim; repeated IDs retain section context. They are not independent ownership claims.", ""])
    for row in rows:
        table.append(f'- **{row["Id"]}** — {row["Section"]}: ' + "; ".join(f"{key}: {value}" for key, value in row["Fields"].items() if key != "ID"))
    outputs["Tasks.md"] = "\n".join(table) + "\n"
    table = ["# Feature scope index", "", "Inventory declarations are research obligations, not qualified support. No automatic PR-title matching or completion inference is performed.", "", "| Format | Family / wave | Scope ID | Feature | Linked tasks |", "| --- | --- | --- | --- | --- |"]
    for scope in scopes:
        scope_claims = [item["TaskId"] for item in links["ScopeLinks"] if item["ScopeId"] == scope["Id"]]
        table.append("| " + " | ".join(markdown_text(value) for value in [scope["Format"], scope["Family"] + " / " + scope["Wave"], scope["Id"], scope["Name"], ", ".join(scope_claims) or "Unmapped — check current claims"]) + " |")
    outputs["Features.md"] = "\n".join(table) + "\n"
    graph = ["flowchart LR"]
    for task in tasks:
        graph.append(f'  {task["Id"]}["{task["Id"]}: {task["Name"].replace(chr(34), chr(39))}"]')
        graph.extend(f'  {dependency} --> {task["Id"]}' for dependency in task["Dependencies"])
    outputs["Dependencies.mmd"] = "\n".join(graph) + "\n"
    outputs["Gantt.svg"] = make_svg(tasks, levels)
    outputs["Gantt.md"] = '# Dependency Gantt\n\nOrdinal dependency tiers; bar widths do not estimate time. Source gates remain binding.\n\n![Dependency Gantt](Gantt.svg)\n\n```mermaid\n' + outputs["Dependencies.mmd"] + '```\n\nSee [task details](Tasks.md), [feature inventory](Features.md) and [maintenance procedure](../README.md).\n'
    table = ["# Open delivery collision inventory", "", f'Observed {snapshot["ObservedOn"]}; contacts are PR authors, not inferred owners. Refresh live head/base/checks before starting work.', "", "| PR | Scope | Contact | Head → base |", "| --- | --- | --- | --- |"]
    heads = {item["headBranch"]: item["number"] for item in snapshot["PullRequests"]}
    for item in snapshot["PullRequests"]:
        parent = f' (stack parent #{heads[item["baseBranch"]]})' if item["baseBranch"] in heads else ""
        table.append(f'| [#{item["number"]}](https://github.com/{snapshot["Repository"]}/pull/{item["number"]}) | {markdown_text(item["title"])} | {markdown_text(item["author"])} | {markdown_text(item["headBranch"])} → {markdown_text(item["baseBranch"])}{parent} |')
    outputs["Deliveries.md"] = "\n".join(table) + "\n"
    schedules = ["gantt", "  title Explicit engineering windows only", "  dateFormat YYYY-MM-DD", "  axisFormat %d %b"]
    for item in links["Schedules"]:
        schedules.append(f'  {item["TaskId"]} :{item["TaskId"]}, {item["Start"]}, {item["Finish"]}')
    outputs["Calendar.md"] = "# Calendar windows\n\n" + ("```mermaid\n" + "\n".join(schedules) + "\n```\n" if links["Schedules"] else "No dated engineering windows have been supplied. Research completion dates are unknown; use the dependency Gantt.\n")
    outputs["Gantt.html"] = '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src \'none\'; style-src \'unsafe-inline\'; img-src \'self\' data:; base-uri \'none\'"><title>Kit planning</title><style>body{font:14px system-ui;color:var(--foreground,#242321)}svg{width:100%;height:auto}a{color:inherit}p{line-height:1.5}</style></head><body><p>Dependency tiers, not dates or durations · snapshot ' + html.escape(links["ObservedOn"]) + '</p>' + outputs["Gantt.svg"] + '<p>Full task gates, catalogue coverage and delivery contacts are in the adjacent Markdown and JSONL files. Missing scope links mean ownership must be checked, not that work is available.</p></body></html>\n'
    board = {"ObservedOn": links["ObservedOn"], "MainRevision": links["MainRevision"], "Links": links,
             "Items": build_schedule(tasks, scopes, rows, snapshot, links, claims, sdk_tasks)}
    outputs["DependencyTiers.svg"] = outputs["Gantt.svg"]
    outputs["Gantt.svg"] = calendar_svg(board["Items"])
    outputs["Gantt.html"] = '<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Scheduled Kit investigations</title></head><body>' + outputs["Gantt.svg"] + '</body></html>\n'
    outputs["Gantt.md"] = '# Scheduled investigation windows\n\nProposed calendar timeboxes, not feature delivery promises. See [the interactive scheduling board](Board.html) for every recorded scope and current delivery.\n\n![Calendar Gantt](Gantt.svg)\n\n## Dependencies\n\n```mermaid\n' + outputs["Dependencies.mmd"] + '```\n\nSource gates and detailed child prerequisites remain binding.\n'
    outputs["BoardData.json"] = json.dumps(board, separators=(",", ":")) + "\n"
    outputs["BoardData.js"] = "window.KitPlanning = " + json.dumps(board, separators=(",", ":")) + ";\n"
    outputs["Board.html"] = '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src \'none\'; script-src \'self\'; style-src \'self\' \'unsafe-inline\'; img-src \'self\' data:; base-uri \'none\'"><title>Kit scheduling board</title><link rel="stylesheet" href="Board.css"></head><body><div id="root"></div><script src="BoardData.js"></script><script src="Board.js"></script></body></html>\n'
    return outputs


def main():
    parser = argparse.ArgumentParser(description="Build deterministic Kit planning views without CAD or network access")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--check", action="store_true", help="Reject stale generated files without writing")
    args = parser.parse_args()
    root = args.root.resolve()
    output = root / "Documentation/Planning/Generated"
    contents = make_outputs(root)
    if args.check:
        stale = [name for name, content in contents.items() if not (output / name).is_file() or (output / name).read_text() != content]
        if stale:
            parser.exit(1, "Stale planning views: " + ", ".join(stale) + "\n")
        print("Planning views match all recorded sources")
        return
    output.mkdir(parents=True, exist_ok=True)
    for name, content in contents.items():
        (output / name).write_text(content, encoding="utf-8", newline="\n")
    print(f"Generated {len(contents)} planning views in {output}")


if __name__ == "__main__":
    main()
