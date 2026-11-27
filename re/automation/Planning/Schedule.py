import hashlib
import json
import re
from datetime import date, timedelta


def next_day(value):
    value += timedelta(days=1)
    while value.weekday() > 4:
        value += timedelta(days=1)
    return value


def identify_rows(rows, identities):
    if identities.get("SchemaVersion") != 1:
        raise ValueError("Unsupported task identity schema")
    registered = {}
    targets = set()
    for entry in identities["Rows"]:
        key = (entry["Source"], entry["TaskId"])
        scope_id = entry["ScopeId"]
        if key in registered or scope_id in targets:
            raise ValueError("Duplicate registered task identity")
        if not re.fullmatch(r"[AB]\d\d[a-z]?(?:-[A-Za-z0-9]+)*:[A-Za-z0-9_-]+", scope_id) or not scope_id.startswith(entry["TaskId"] + ":"):
            raise ValueError("Invalid registered scope ID")
        registered[key] = scope_id
        targets.add(scope_id)
    identified = []
    seen_keys = set()
    seen_ids = set()
    for row in rows:
        key = (row["Source"], row["Id"])
        if key in seen_keys:
            raise ValueError("Duplicate source task identity: " + str(key))
        seen_keys.add(key)
        scope_id = registered.get(key)
        if scope_id is None:
            scope_id = row["Id"] + ":" + hashlib.sha256(json.dumps(key, separators=(",", ":")).encode()).hexdigest()[:12]
            if scope_id in targets:
                raise ValueError("Generated task identity collides with registered history")
        if scope_id in seen_ids:
            raise ValueError("Duplicate generated scope ID")
        seen_ids.add(scope_id)
        identified.append({**row, "ScopeId": scope_id})
    return identified


def build_schedule(tasks, scopes, rows, snapshot, links, claims, sdk_tasks):
    items = []
    for task in tasks:
        items.append({**task, "Area": task.get("Area", "Project"), "Kind": "Milestone", "Stages": {}})
    for row in rows:
        if row["Id"] in {task["Id"] for task in tasks}:
            continue
        fields = row["Fields"]
        items.append({"Id": row["ScopeId"], "Name": fields.get("Deliverable", fields.get("Scope", row["Section"])),
                      "Area": "Project", "Kind": "Research task", "Owner": fields.get("Owner", "See owning register"),
                      "Status": fields.get("Status", "unverified"), "Dependencies": [], "Source": row["Source"],
                      "Exit": fields.get("Exit criterion or remaining evidence", fields.get("Evidence or remaining requirement", fields.get("Exit condition", "See source register"))), "Stages": {}})
    contacts = {"PR" + str(item["number"]): item["author"] for item in snapshot["PullRequests"] if item.get("state", "open") == "open"}
    for scope in scopes:
        active_links = [link for link in scope["TaskLinks"] if link["TaskId"] in contacts and any(stage["Status"] in {"active", "checking"} for stage in link["Stages"].values())]
        items.append({"Id": scope["Id"], "Name": scope["Family"] + " / " + scope["Name"], "Area": scope["Format"],
                      "Kind": "Native decoding domain" if scope["Definition"].get("kind") == "native_type" else "API declaration" if not scope.get("ScheduleEligible", True) else "Decoding scope", "Owner": "Bounded work: " + ", ".join(sorted({contacts[link["TaskId"]] for link in active_links})) if active_links else "Unassigned — refresh claims", "Status": "active" if active_links else "unverified",
                      "Dependencies": [], "Source": scope["Source"], "Exit": scope["Definition"], "Stages": scope["TaskLinks"], "Tracks": {track: [link for link in scope["TaskLinks"] if stage in link["Stages"]] or "unverified" for track, stage in {"Read": "decode", "Write": "write", "Conversion preparation": "semantics"}.items()},
                      "ScheduleEligible": scope.get("ScheduleEligible", True), "Wave": scope["Wave"], "FamilyDependencies": scope["FamilyDependencies"]})
    for delivery in snapshot["PullRequests"]:
        items.append({"Id": "PR" + str(delivery["number"]), "Name": delivery["title"], "Area": "Delivery",
                      "Kind": "Open PR" if delivery["state"] == "open" else "Merged PR" if delivery["state"] == "merged" else "Closed PR", "Owner": delivery["author"], "Status": "open" if delivery["state"] == "open" else "complete" if delivery["state"] == "merged" else "cancelled",
                      "Dependencies": [], "Source": delivery["url"], "Exit": "Fresh current-head checks, configured review and queue acceptance remain separate",
                      "Stages": {}, "Head": delivery["headBranch"], "Base": delivery["baseBranch"]})
    items.extend({**claim, "Area": "Project", "Kind": "Research claim", "Dependencies": [], "Exit": claim["Excerpt"], "Stages": {}, "ScheduleEligible": False} for claim in claims)
    items.extend(sdk_tasks)
    origin = date.fromisoformat(links["SchedulePolicy"]["Start"])
    duration = links["SchedulePolicy"]["TimeboxDays"]
    if not 1 <= duration <= 60 or origin.weekday() > 4:
        raise ValueError("Schedule requires a working-day origin and a bounded timebox")
    pools = {area: [origin] * count for area, count in links["SchedulePolicy"]["ParallelLanes"].items()}
    if any(not pool or len(pool) > 16 for pool in pools.values()):
        raise ValueError("Planning lane capacity must be between one and sixteen")
    ends = {}
    overrides = {entry["TaskId"]: entry for entry in links["Schedules"]}
    pending = list(items)
    while pending:
        eligible = next((item for item in pending if all(dependency in ends for dependency in item["Dependencies"])), None)
        if eligible is None:
            raise ValueError("Unknown or cyclic scheduling dependencies")
        item = eligible
        pending.remove(item)
        if (not links["SchedulePolicy"].get("ForecastEnabled", False) or item["Kind"] in {"Open PR", "Merged PR", "Closed PR"} or item["Status"].lower() in {"complete", "cancelled", "superseded"} or not item.get("ScheduleEligible", True)) and item["Id"] not in overrides:
            item.update(Start=None, Finish=None, ScheduleKind="Observed or inventory-only scope; no dates asserted")
            ends[item["Id"]] = origin
            continue
        pool = pools[item["Area"]]
        lane = pool.index(min(pool))
        start = max([pool[lane], *[ends[dependency] for dependency in item["Dependencies"]]])
        while start.weekday() > 4:
            start = next_day(start)
        finish = start
        for _ in range(duration - 1):
            finish = next_day(finish)
        if item["Id"] in overrides:
            start = date.fromisoformat(overrides[item["Id"]]["Start"])
            finish = date.fromisoformat(overrides[item["Id"]]["Finish"])
        item.update(Start=start.isoformat(), Finish=finish.isoformat(),
                    ScheduleKind="Supplied window" if item["Id"] in overrides else "Proposed investigation timebox",
                    Lane=f'{item["Area"]} {lane + 1}', Basis=overrides.get(item["Id"], {}).get("Basis", links["SchedulePolicy"]["Basis"]))
        pool[lane] = next_day(finish)
        ends[item["Id"]] = next_day(finish)
    return items
