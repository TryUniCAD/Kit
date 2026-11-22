from ChamferModel import compare_six
from RunSweepSources import driver_identity, stable_owners, topology_signature
from SweepModel import PATH, SECTION, require
from SweepPacket import digest


def projection(state):
    body = state["body"]
    values = body["native"]
    count, faces = topology_signature(body)
    return {"tree": state["tree"], "configuration": state["configuration"], "definition": state["definition"],
            "drivers": {key: [list(value[0]), *value[1:]] for key, value in driver_identity(state).items()},
            "driver_metres": {key: value["value_m"] for key, value in state["drivers"].items()},
            "topology": [list(count), [list(row) for row in faces]],
            "scalars": {key: values[key] for key in ("volume", "area", "mass")},
            "com": values["com"], "bounds": body["bounds_m"]}


def compare_source(state, expected):
    actual = projection(state)
    equal = ("tree", "configuration", "definition", "drivers", "driver_metres", "topology")
    different = [key for key in equal if actual[key] != expected[key]]
    require(not different, f"independent source ownership differs: {different}")
    checked = 0
    for key, tolerance in (("volume", 1e-21), ("area", 1e-16), ("mass", 1e-17)):
        require(compare_six(actual["scalars"][key], expected["scalars"][key], tolerance)[2],
                f"independent source {key} differs at six significant figures")
        checked += 1
    for label, values, other in (("COM", actual["com"], expected["com"]),
                                 ("bounds", sum(actual["bounds"], []), sum(expected["bounds"], []))):
        for index, (value, target) in enumerate(zip(values, other, strict=True)):
            require(compare_six(value, target, 1e-10)[2], f"independent source {label}[{index}] differs")
            checked += 1
    return checked


def lifecycle(original, derivatives, records, expected):
    first = records["candidate-open"]
    baseline = first["reopened"]
    require(digest(original) == first["native_sha256"], "generated candidate changed on close")
    hashes = {"original": first["native_sha256"]}
    checked = compare_source(baseline, expected["original"])
    for role, untouched in (("section", PATH), ("path", SECTION)):
        edit, reopen = (records[f"{role}-{action}"] for action in ("edit", "reopen"))
        hashes[role] = edit["native_sha256"]
        require(digest(derivatives[role]) == hashes[role] == reopen["native_sha256"],
                "candidate edited save changed on fresh reopen")
        states = (edit["reopened"], edit["edited"], reopen["reopened"])
        require(all(stable_owners(state, baseline) for state in states)
                and all(state["drivers"][untouched]["value_m"] == baseline["drivers"][untouched]["value_m"] for state in states)
                and all(topology_signature(phase["before_explicit_rebuild"]) == topology_signature(baseline["body"])
                        for phase in (edit, reopen)), "same candidate changed topology, ownership or the other driver")
        for state, source_role in zip(states, ("original", role, role), strict=True):
            checked += compare_source(state, expected[source_role])
    require(len(set(hashes.values())) == len(hashes), "each independent edit requires a distinct persisted save")
    return {"candidate_sha256": hashes, "paired_numeric_checks": checked}
