# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from InferenceGrid.FeatureRoutes import FeatureRecipes
from InferenceGrid.ScopeOrder import OrderScopes
from Records import digest


# aliases across both catalogues must share the same underlying controller work
def BuildRunPlan(Catalogues, Revision):
    Features, Scopes = {}, {}
    Pins = {}
    for Source, Catalogue in sorted(Catalogues.items()):
        Pins[Source] = Catalogue["catalogue_sha256"]
        Entries = {}
        for Identity, Plan in sorted(Catalogue["features"].items()):
            Entry = {"plan_id": Plan["plan_id"]}
            Recipe = FeatureRecipes.get(Identity)
            if "recipe_spec" in Plan:
                Entry["recipe_spec"] = Plan["recipe_spec"]
            if Recipe is None:
                Waiting = Plan["blockers"] == ["pinned_native_evidence_required"]
                Entry.update(
                    status="awaiting_capture" if Waiting else "recipe_unavailable",
                    blockers=Plan["blockers"],
                )
                if "available_evidence" in Plan:
                    Entry["available_evidence"] = Plan["available_evidence"]
            else:
                if Plan["route"]["scope"] != Recipe.Scope:
                    raise ValueError("catalogue route differs from the reviewed recipe")
                Chosen = Scopes.setdefault(Recipe.Scope, Identity)
                if FeatureRecipes[Chosen] != Recipe:
                    raise ValueError("multiple recipes use the same assessment scope")
                Entry.update(status="planned", scope=Recipe.Scope)
            Entries[Identity] = Entry
        Features[Source] = Entries
    return {
        "schema_version": 1,
        "source_revision": Revision,
        "catalogues": Pins,
        "inputs_sha256": digest([Revision, Pins]),
        "features": Features,
        "scopes": dict(sorted(Scopes.items())),
        "scope_order": OrderScopes(Catalogues, Scopes),
    }


# completeness distinguishes unavailable routes from finished decoder attempts
def RunOutcome(Plan, Results, SupervisorFailures):
    Counts = {}
    for Source, Entries in Plan["features"].items():
        Counts[Source] = {}
        for Entry in Entries.values():
            State = Entry["status"]
            if "scope" in Entry:
                State = Results[Entry["scope"]]["status"]
            Counts[Source][State] = Counts[Source].get(State, 0) + 1
    Failed = bool(SupervisorFailures) or any(
        Row["status"] == "failed" for Row in Results.values()
    )
    Complete = all(set(Statuses) <= {"completed"} for Statuses in Counts.values())
    Status = "failed" if Failed else "completed" if Complete else "coverage_incomplete"
    return {
        "schema_version": 1,
        "plan_sha256": digest(Plan),
        "status": Status,
        "features": Counts,
        "scopes": Results,
        "supervisor_failures": SupervisorFailures,
    }
