# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


# native feature owners and dimensions distinguish a reference plane from equal mass lookalikes
def CheckFeatureTree(Check, Observation, Path):
    Features = Check.Field(Observation, "feature_tree", Path)
    if not isinstance(Features, list):
        Check.Add(
            Path + ".feature_tree",
            "native feature list",
            Features,
            "verifier_support_missing",
        )
        return
    Names = [Feature.get("name") for Feature in Features if isinstance(Feature, dict)]
    if len(Names) != len(Features) or len(set(Names)) != len(Names):
        Check.Add(Path + ".feature_tree.names", "unique native feature names", Names)
        return
    Required = {
        **Check.Expectations["prerequisite_feature_types"],
        "RecipeFeature": "RefPlane",
    }
    for Name, Type in Required.items():
        if Name not in Names:
            Check.Add(Path + ".feature_tree." + Name, Type, "missing")
    if set(Required) <= set(Names) and not Names.index("SeedProfile") < Names.index(
        "SeedFeature"
    ) < Names.index("RecipeFeature"):
        Check.Add(Path + ".feature_tree.order", list(Required), Names)
    for Feature in Features:
        FeaturePath = Path + ".feature_tree." + Feature["name"]
        Check.Equal(
            Check.Field(Feature, "suppressed", FeaturePath),
            False,
            FeaturePath + ".suppressed",
        )
        Check.Equal(
            Check.Field(Feature, "error_code", FeaturePath),
            0,
            FeaturePath + ".error_code",
        )
        Check.Equal(
            Check.Field(Feature, "warning", FeaturePath),
            False,
            FeaturePath + ".warning",
        )
        Name = Feature["name"]
        if Name not in Required:
            continue
        Check.Equal(
            Check.Field(Feature, "type", FeaturePath),
            Required[Name],
            FeaturePath + ".type",
        )
        Parents = Check.Field(Feature, "parents", FeaturePath)
        Parent = "SeedProfile" if Name == "SeedFeature" else "Front Plane"
        if not isinstance(Parents, list) or Parent not in Parents:
            Check.Add(FeaturePath + ".parents", {"contains": Parent}, Parents)
        if Name == "SeedFeature":
            Operation = Check.Field(Feature, "operation", FeaturePath)
            if not isinstance(Operation, dict):
                Check.Add(
                    FeaturePath + ".operation",
                    "collected extrusion definition",
                    Operation,
                    "verifier_support_missing",
                )
                continue
            for Field, Expected in {
                "kind": "extrude",
                "end_condition": 0,
                "reverse_direction": False,
                "both_directions": False,
            }.items():
                Check.Equal(
                    Check.Field(Operation, Field, FeaturePath + ".operation"),
                    Expected,
                    FeaturePath + ".operation." + Field,
                )
            Check.Near(
                Check.Field(Operation, "depth_m", FeaturePath + ".operation"),
                0.01,
                FeaturePath + ".operation.depth_m",
                "native_metres",
            )
        if Name == "SeedProfile":
            Dimensions = Check.Field(Feature, "dimensions", FeaturePath)
            for Parameter, Value in {"width_mm": 0.04, "height_mm": 0.02}.items():
                Matches = [
                    Item
                    for Item in Dimensions or []
                    if isinstance(Item, dict) and Item.get("name") == Parameter
                ]
                if len(Matches) != 1:
                    Check.Add(
                        FeaturePath + ".dimensions." + Parameter,
                        "one owned driving dimension",
                        Matches,
                    )
                    continue
                Check.Equal(
                    Check.Field(Matches[0], "driven_state", FeaturePath),
                    2,
                    FeaturePath + ".dimensions." + Parameter + ".driven_state",
                )
                Check.Near(
                    Check.Field(Matches[0], "system_value", FeaturePath),
                    Value,
                    FeaturePath + ".dimensions." + Parameter + ".system_value",
                    "native_metres",
                )


# support transform and actual definition fields prove the requested operation independently
def CheckPlane(Check, Observation, Offset, Path):
    Plane = Check.Field(Observation, "plane", Path)
    if not isinstance(Plane, dict):
        Check.Add(
            Path + ".plane", "collected native plane", Plane, "verifier_support_missing"
        )
        return
    Errors = Check.Field(Plane, "collection_errors", Path + ".plane")
    if Errors != {}:
        Check.Add(
            Path + ".plane.collection_errors", {}, Errors, "verifier_support_missing"
        )
    Frozen = Check.Expectations["plane"]
    for Field in ("name", "type"):
        Check.Equal(
            Check.Field(Plane, Field, Path + ".plane"),
            Frozen[Field],
            Path + ".plane." + Field,
        )
    Check.Vector(
        Check.Field(Plane, "origin_mm", Path + ".plane"),
        [0.0, 0.0, Offset],
        Path + ".plane.origin_mm",
    )
    Check.Vector(
        Check.Field(Plane, "normal_world", Path + ".plane"),
        Frozen["normal_world"],
        Path + ".plane.normal_world",
        "normal",
    )
    Transform = Check.Field(Plane, "transform", Path + ".plane")
    if not isinstance(Transform, list) or len(Transform) != 16:
        Check.Add(
            Path + ".plane.transform",
            "sixteen native transform values",
            Transform,
            "verifier_support_missing",
        )
    Definition = Check.Field(Plane, "definition", Path + ".plane")
    if not isinstance(Definition, dict):
        Check.Add(
            Path + ".plane.definition",
            "native plane feature definition",
            Definition,
            "verifier_support_missing",
        )
        return
    for Field, Expected in {
        "type": Frozen["definition_type"],
        "type2": Frozen["definition_type2"],
        "reverse_direction": False,
        "selection_count": 1,
    }.items():
        Check.Equal(
            Check.Field(Definition, Field, Path + ".plane.definition"),
            Expected,
            Path + ".plane.definition." + Field,
        )
    Check.Near(
        Check.Field(Definition, "distance_m", Path + ".plane.definition"),
        Offset / 1000,
        Path + ".plane.definition.distance_m",
        "native_metres",
    )
    Constraints = Check.Field(Definition, "constraints", Path + ".plane.definition")
    Check.Equal(
        Constraints,
        [Frozen["distance_constraint"]],
        Path + ".plane.definition.constraints",
    )
    References = Check.Field(Definition, "references", Path + ".plane.definition")
    if not isinstance(References, list) or len(References) != 1:
        Check.Add(
            Path + ".plane.definition.references",
            "one actual support reference",
            References,
        )
    else:
        Check.Equal(
            References[0].get("name"),
            Frozen["support_name"],
            Path + ".plane.definition.references[0].name",
        )
        Check.Equal(
            References[0].get("type"),
            Frozen["support_type"],
            Path + ".plane.definition.references[0].type",
        )
        Check.Vector(
            Check.Field(
                References[0], "origin_mm", Path + ".plane.definition.references[0]"
            ),
            [0.0, 0.0, 0.0],
            Path + ".plane.definition.references[0].origin_mm",
        )
        Check.Vector(
            Check.Field(
                References[0], "normal_world", Path + ".plane.definition.references[0]"
            ),
            [0.0, 0.0, 1.0],
            Path + ".plane.definition.references[0].normal_world",
            "normal",
        )
    Bindings = Check.Field(Observation, "parameter_bindings", Path)
    Binding = Bindings.get("offset_mm") if isinstance(Bindings, dict) else None
    if not isinstance(Binding, dict):
        Check.Add(
            Path + ".parameter_bindings.offset_mm",
            "one actual driving offset dimension",
            Binding,
        )
        return
    for Field, Expected in {
        "owner": "RecipeFeature",
        "name": "offset_mm",
        "driven_state": 2,
    }.items():
        Check.Equal(
            Check.Field(Binding, Field, Path),
            Expected,
            Path + ".parameter_bindings.offset_mm." + Field,
        )
    FullName = Check.Field(Binding, "full_name", Path)
    if not isinstance(FullName, str) or not FullName.startswith(
        "offset_mm@RecipeFeature"
    ):
        Check.Add(
            Path + ".parameter_bindings.offset_mm.full_name",
            "offset_mm@RecipeFeature...",
            FullName,
        )
    Check.Near(
        Check.Field(Binding, "system_value", Path),
        Offset / 1000,
        Path + ".parameter_bindings.offset_mm.system_value",
        "native_metres",
    )
    Check.Near(
        Check.Field(Binding, "value_mm", Path),
        Offset,
        Path + ".parameter_bindings.offset_mm.value_mm",
    )


# unchanged mass is only a prerequisite and cannot establish that the feature is correct
def CheckObservation(Check, Observation, Offset, Path):
    if not isinstance(Observation, dict):
        Check.Add(Path, "native measurements", Observation, "verifier_support_missing")
        return
    for Field in ("body_count", "surface_body_count"):
        Check.Equal(
            Check.Field(Observation, Field, Path),
            Check.Expectations["geometry"][Field],
            Path + "." + Field,
        )
    Check.Near(
        Check.Field(Observation, "volume_mm3", Path),
        Check.Expectations["geometry"]["volume_mm3"],
        Path + ".volume_mm3",
        "volume_mm3",
    )
    for Field in ("center_of_mass_mm", "bounds_mm"):
        Check.Vector(
            Check.Field(Observation, Field, Path),
            Check.Expectations["geometry"][Field],
            Path + "." + Field,
        )
    Check.Equal(Check.Field(Observation, "units_code", Path), 5, Path + ".units_code")
    CheckFeatureTree(Check, Observation, Path)
    CheckPlane(Check, Observation, Offset, Path)
    Sketches = Check.Field(Observation, "sketches", Path)
    if not isinstance(Sketches, list) or len(Sketches) != 1:
        Check.Add(Path + ".sketches", "one prerequisite sketch", Sketches)
    else:
        Sketch = Sketches[0]
        for Field, Expected in {
            "name": "SeedProfile",
            "fully_defined": True,
            "constraint_status": 3,
            "support_name": "Front Plane",
            "support_type": 4,
            "region_count": 1,
        }.items():
            Check.Equal(
                Check.Field(Sketch, Field, Path + ".sketches[0]"),
                Expected,
                Path + ".sketches[0]." + Field,
            )
        Check.Near(
            Check.Field(Sketch, "section_area_mm2", Path + ".sketches[0]"),
            800.0,
            Path + ".sketches[0].section_area_mm2",
        )
