from datetime import date, timedelta


def next_day(value):
    value += timedelta(days=1)
    while value.weekday() > 4:
        value += timedelta(days=1)
    return value


def build_schedule(tasks, scopes, rows, snapshot, links):
    items = []
    for task in tasks:
        items.append({**task, "Area": task.get("Area", "Project"), "Kind": "Milestone", "Stages": {}})
    for number, row in enumerate(rows):
        if row["Id"] in {task["Id"] for task in tasks}:
            continue
        fields = row["Fields"]
        items.append({"Id": f'{row["Id"]}:{number}', "Name": fields.get("Deliverable", fields.get("Scope", row["Section"])),
                      "Area": "Project", "Kind": "Research task", "Owner": fields.get("Owner", "See owning register"),
                      "Status": fields.get("Status", "unverified"), "Dependencies": [], "Source": row["Source"],
                      "Exit": fields.get("Exit criterion or remaining evidence", fields.get("Evidence or remaining requirement", fields.get("Exit condition", "See source register"))), "Stages": {}})
    for scope in scopes:
        items.append({"Id": scope["Id"], "Name": scope["Family"] + " / " + scope["Name"], "Area": scope["Format"],
                      "Kind": "Decoding scope", "Owner": "Unassigned — refresh claims", "Status": "unverified",
                      "Dependencies": [], "Source": scope["Source"], "Exit": scope["Definition"], "Stages": scope["TaskLinks"],
                      "Wave": scope["Wave"], "FamilyDependencies": scope["FamilyDependencies"]})
    for delivery in snapshot["PullRequests"]:
        items.append({"Id": "PR" + str(delivery["number"]), "Name": delivery["title"], "Area": "Delivery",
                      "Kind": "Open PR", "Owner": delivery["author"], "Status": "open",
                      "Dependencies": [], "Source": delivery["url"], "Exit": "Fresh current-head checks, configured review and queue acceptance remain separate",
                      "Stages": {}, "Head": delivery["headBranch"], "Base": delivery["baseBranch"]})
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
        if item["Kind"] == "Open PR" or item["Status"].lower() == "complete":
            item.update(Start=None, Finish=None, ScheduleKind="Observed work; no dates asserted")
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
