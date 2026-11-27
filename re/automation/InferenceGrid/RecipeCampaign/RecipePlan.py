# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from hashlib import sha256
from json import loads
from pathlib import Path

from InferenceGrid.Authoring.ReadCases import MakeCase
from InferenceGrid.FeatureSpecs import SpecFor, UniqueFields
from Records import digest


# source pins identify the exact bounded bytes supplied to the assistant
def SourcePin(SourceRoot, Relative):
    Root = Path(SourceRoot).resolve()
    Source = Root / Relative
    if Source.is_symlink() or not Source.is_file():
        raise ValueError(f"campaign source must be a regular file: {Relative}")
    if not Source.resolve().is_relative_to(Root):
        raise ValueError("campaign source escapes the selected checkout")
    with Source.open("rb") as Stream:
        Raw = Stream.read(4 * 1024 * 1024 + 1)
    if not Raw or len(Raw) > 4 * 1024 * 1024:
        raise ValueError(f"campaign source exceeds its byte boundary: {Relative}")
    return Raw, {"sha256": sha256(Raw).hexdigest(), "size_bytes": len(Raw)}


# guarded authoring selection must succeed before a written recipe becomes executable
def RecipeBinding(Application, Aliases, RecipeKey):
    for ModeValue in ("discovery", "qualification", "holdout"):
        for FeatureKey in Aliases:
            try:
                Written = SpecFor(FeatureKey)
                if Written is None or Written["id"] != RecipeKey:
                    raise ValueError("written recipe differs from the loaded executor")
                Binding = MakeCase(Application, FeatureKey, {}, ModeValue)
            except (
                OSError,
                ValueError,
                TypeError,
                KeyError,
                RuntimeError,
                ImportError,
            ) as Error:
                return None, None, f"{type(Error).__name__}: {Error}"
            if Binding is not None:
                return ModeValue, Binding, None
    return None, None, None


# aliases share one pending task while preserving application and recipe source identity
def PlanRecipes(SourceRoot, Catalogues):
    SourceName = "re/automation/FeatureRecipeSpecs.json"
    Raw, Pin = SourcePin(SourceRoot, SourceName)
    Written = loads(Raw, object_pairs_hook=UniqueFields)
    if (
        not isinstance(Written, dict)
        or type(Written.get("schema_version")) is not int
        or Written["schema_version"] != 1
        or not isinstance(Written.get("recipes"), list)
        or not isinstance(Written.get("seeds"), dict)
        or not isinstance(Written.get("conventions"), list)
    ):
        raise ValueError("unsupported campaign recipe specification")
    Entries, Pins, Unmapped = {}, {SourceName: Pin}, {}
    Seen = set()
    for Row in Written["recipes"]:
        if (
            not isinstance(Row, dict)
            or not isinstance(Row.get("id"), str)
            or not Row["id"]
            or Row["id"] in Seen
            or not isinstance(Row.get("entries"), dict)
        ):
            raise ValueError(
                "campaign recipes require unique identities and entry maps"
            )
        Seen.add(Row["id"])
    for Application, Catalogue in sorted(Catalogues.items()):
        if Application not in ("solidworks", "fusion"):
            raise ValueError("campaign catalogue has an unsupported application")
        Selected = set(Catalogue["features"])
        Covered = set()
        Pins[f"catalogue:{Application}"] = {"sha256": Catalogue["catalogue_sha256"]}
        for Row in Written["recipes"]:
            AppEntries = Row["entries"].get(Application, [])
            if not isinstance(AppEntries, list) or any(
                not isinstance(FeatureKey, str) for FeatureKey in AppEntries
            ):
                raise ValueError("recipe application entries must be feature labels")
            Aliases = sorted(Selected.intersection(AppEntries))
            if not Aliases:
                continue
            if Covered.intersection(Aliases):
                raise ValueError("campaign feature belongs to multiple written recipes")
            Covered.update(Aliases)
            Key = digest([Application, Row["id"]])[:16]
            ModeValue, Binding, Error = RecipeBinding(Application, Aliases, Row["id"])
            SeedKey = Row.get("seed")
            if SeedKey not in (None, "none") and SeedKey not in Written["seeds"]:
                raise ValueError("campaign recipe references an unknown seed")
            Entries[Key] = {
                "key": Key,
                "application": Application,
                "recipe_id": Row["id"],
                "aliases": Aliases,
                "recipe": Row,
                "row_sha256": digest(Row),
                "conventions": Written["conventions"],
                "seed": Written["seeds"].get(SeedKey),
                "status": "pending",
                "mode": ModeValue,
                "binding": Binding,
                "needs_assistant": Binding is None,
                "assistant_error": Error,
            }
        Unmapped[Application] = sorted(Selected - Covered)
    return {
        "schema_version": 1,
        "entries": dict(sorted(Entries.items())),
        "input_pins": Pins,
        "unmapped": Unmapped,
    }
