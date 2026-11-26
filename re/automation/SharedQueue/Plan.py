# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from graphlib import CycleError, TopologicalSorter

from Records import bounded, canonical, digest, label, specification


# request validation prevents stale clients and malformed batches from changing subscriptions
def request_plan(value):
    required = {"queue_version", "request", "revision", "jobs"}
    if (
        not isinstance(value, dict)
        or not required <= value.keys()
        or value.keys() - required - {"priority"}
    ):
        raise ValueError("shared request fields do not match the version 1 contract")
    if type(value["queue_version"]) is not int or value["queue_version"] != 1:
        raise ValueError("shared request must use queue version 1")
    request = label(value["request"])
    revision = bounded(value["revision"], 0, 2**63 - 1)
    priority = bounded(value.get("priority", 50), 0, 100)
    jobs = value["jobs"]
    if not isinstance(jobs, list) or not 1 <= len(jobs) <= 1000:
        raise ValueError("shared request must contain 1–1000 jobs")
    specs = [specification(job) for job in jobs]
    if len({spec["id"] for spec in specs}) != len(specs):
        raise ValueError("shared request contains duplicate local job identifiers")
    normalized = {
        "queue_version": 1,
        "request": request,
        "revision": revision,
        "priority": priority,
        "jobs": sorted(specs, key=lambda item: item["id"]),
    }
    canonical(normalized)
    return normalized


# dependency names must become canonical before a downstream job receives its identity
def canonical_jobs(specs):
    original = {spec["id"]: spec for spec in specs}
    graph = {
        name: set(spec["depends_on"]) & original.keys()
        for name, spec in original.items()
    }
    try:
        order = tuple(TopologicalSorter(graph).static_order())
    except CycleError as error:
        raise ValueError("shared request contains a dependency cycle") from error
    aliases, shared = {}, {}
    for name in order:
        spec = original[name]
        normalized = {
            **spec,
            "depends_on": sorted(
                {aliases.get(parent, parent) for parent in spec["depends_on"]}
            ),
        }
        normalized["inputs"] = {
            role: (
                {
                    **binding,
                    "dependency": aliases.get(
                        binding["dependency"], binding["dependency"]
                    ),
                }
                if isinstance(binding, dict)
                else binding
            )
            for role, binding in spec["inputs"].items()
        }
        identity = "shared:" + digest(
            {key: item for key, item in normalized.items() if key != "id"}
        )
        aliases[name] = identity
        shared[identity] = {**normalized, "id": identity}
    return aliases, list(shared.values())
