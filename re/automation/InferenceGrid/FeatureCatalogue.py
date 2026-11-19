# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import hashlib
import json
from graphlib import TopologicalSorter

from InferenceGrid.FeatureRoutes import DescribeRecipe, FeatureRecipes
from Records import digest, label

# the published planning export fits inside an explicit read boundary
CatalogueBytes = 2 * 1024 * 1024


# planning input must have one authoritative value for every field
def UniqueFields(Pairs):
    Values = dict(Pairs)
    if len(Values) != len(Pairs):
        raise ValueError("catalogue contains a duplicate field")
    return Values


# catalogue references must be unambiguous labels to preserve an accurate plan
def References(Items):
    if not isinstance(Items, list):
        raise ValueError("catalogue references must be an array")
    Values = [label(Item) for Item in Items]
    if len(Values) != len(set(Values)):
        raise ValueError("catalogue contains duplicate references")
    return sorted(Values)


# complete plans retain the source pin separately from each feature identity
def ReadCatalogue(CataloguePath, Expected):
    if not CataloguePath.is_file():
        raise ValueError("catalogue must be a regular JSON file")
    with CataloguePath.open("rb") as Source:
        Raw = Source.read(CatalogueBytes + 1)
    if not 0 < len(Raw) <= CatalogueBytes:
        raise ValueError("catalogue exceeds the supported byte limit")
    Pin = hashlib.sha256(Raw).hexdigest()
    if Expected is not None and Expected != Pin:
        raise ValueError("catalogue SHA-256 does not match the expected input")
    Root = json.loads(Raw, object_pairs_hook=UniqueFields)
    if (
        not isinstance(Root, dict)
        or type(Root.get("schema_version")) is not int
        or Root["schema_version"] != 1
    ):
        raise ValueError("unsupported SOLIDWORKS catalogue schema")
    Families, Features = CatalogueEntries(Root)
    return {
        "schema_version": 1,
        "catalogue_sha256": Pin,
        "families": Families,
        "features": Features,
    }


# the catalogue preserves taxonomy seams without making family labels runnable
def CatalogueEntries(Root):
    Families, Features = {}, {}
    Rows = Root["families"]
    if not isinstance(Rows, list) or not Rows:
        raise ValueError("catalogue must contain at least one feature family")
    Waves = References([Wave["id"] for Wave in Root["waves"]])
    for Family in Rows:
        Identity = label(Family["id"])
        Wave = label(Family["wave"])
        if Identity in Families or Wave not in Waves:
            raise ValueError("catalogue repeats a family or selects an unknown wave")
        Dependencies = References(Family["dependencies"])
        Parent = Family["parent_id"]
        if Parent is not None:
            Parent = label(Parent)
        Families[Identity] = {
            "parent": Parent,
            "wave": Wave,
            "dependencies": Dependencies,
        }
        if not isinstance(Family["subfeatures"], list):
            raise ValueError("catalogue subfeatures must be an array")
        for Feature in Family["subfeatures"]:
            Key = label(Feature["id"])
            if Key in Features or not Key.startswith(Identity + ":"):
                raise ValueError(
                    "catalogue repeats a feature or binds it to the wrong family"
                )
            Features[Key] = FeaturePlan(Identity, Wave, Dependencies, Feature)
    ValidateDependencies(Families, Features)
    return dict(sorted(Families.items())), dict(sorted(Features.items()))


# unknown planning dependencies must stay visible as input errors before dispatch
def ValidateDependencies(Families, Features):
    for Group in Families.values():
        if set(Group["dependencies"]) - Families.keys() or (
            Group["parent"] is not None and Group["parent"] not in Families
        ):
            raise ValueError("catalogue family refers to an unknown prerequisite")
    for Plan in Features.values():
        if set(Plan["dependencies"]) - Families.keys():
            raise ValueError("catalogue feature refers to an unknown prerequisite")
    TopologicalSorter(
        {
            Key: Group["dependencies"] + ([Group["parent"]] if Group["parent"] else [])
            for Key, Group in Families.items()
        }
    ).prepare()


# each entry gets a stable plan while only reviewed recipes get executable work
def FeaturePlan(Identity, Wave, FamilyDependencies, Feature):
    Key = Feature["id"]
    Recipe = FeatureRecipes.get(Key)
    Options = Feature["options"]
    if not isinstance(Options, list) or any(
        not isinstance(Option, str) or not Option or len(Option) > 256
        for Option in Options
    ):
        raise ValueError("catalogue contains an invalid option axis")
    Plan = {
        "feature": Key,
        "family": Identity,
        "wave": Wave,
        "dependencies": sorted(
            set(FamilyDependencies) | set(References(Feature["dependencies"]))
        ),
        "option_axes": sorted(set(Options)),
        "status": "mapped" if Recipe else "blocked",
        "route": DescribeRecipe(Recipe) if Recipe else None,
        "blockers": [] if Recipe else ["reviewed_recipe_and_pinned_evidence_required"],
    }
    return {**Plan, "plan_id": digest(Plan)}
