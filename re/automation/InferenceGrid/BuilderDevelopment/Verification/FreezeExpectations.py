# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from hashlib import sha256
from json import dumps
from math import isfinite
from pathlib import Path
from re import fullmatch


# canonical hashes make expectation and reservation mutation detectable at verification time
def RecordHash(Value):
    return sha256(
        dumps(Value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


# the collector and generated builder cannot silently substitute a changed verifier
def VerifierPins():
    Directory = Path(__file__).resolve().parent
    return {
        File.name: sha256(File.read_bytes()).hexdigest()
        for File in sorted(Directory.glob("*.py"))
    }


# the control is independent retained native evidence rather than a candidate supplied target
def DefaultControl():
    return {
        "native_sha256": "d1bbca099ccac1330024619390df3c6b76320a6a6c281a5009578b2fb63e7408",
        "body_count": 1,
        "volume_mm3": 881814.3482038013,
        "center_of_mass_mm": [
            0.034225857556205885,
            -0.01787822757779362,
            9.88216068003808,
        ],
    }


# only the reviewed positive single plane scope can be frozen for this first feature
def FreezeExpectations(Cases, ApplicationBuild, SourcePin=None, Control=None):
    if not isinstance(Cases, list) or not 1 <= len(Cases) <= 3:
        raise ValueError("plane expectations require one to three cases")
    if not isinstance(ApplicationBuild, str) or not ApplicationBuild.strip():
        raise ValueError("plane expectations require an exact application build")
    Normal, Identities = [], set()
    for Case in Cases:
        if not isinstance(Case, dict) or set(Case) != {"id", "offset_mm", "edit_mm"}:
            raise ValueError("plane cases require id offset_mm and edit_mm")
        Identity = Case["id"]
        if (
            not isinstance(Identity, str)
            or not fullmatch(r"[A-Za-z0-9_-]{1,64}", Identity)
            or Identity in Identities
        ):
            raise ValueError("plane case identities must be unique bounded labels")
        for Name in ("offset_mm", "edit_mm"):
            Value = Case[Name]
            if (
                type(Value) not in (int, float)
                or not isfinite(Value)
                or not 0.01 <= Value <= 1000
            ):
                raise ValueError(
                    "plane offsets must be finite positive millimetres within the frozen scope"
                )
        if Case["offset_mm"] == Case["edit_mm"]:
            raise ValueError("plane edit must change its driving value")
        Identities.add(Identity)
        Normal.append(
            {
                "id": Identity,
                "offset_mm": float(Case["offset_mm"]),
                "edit_mm": float(Case["edit_mm"]),
            }
        )
    ExpectedControl = DefaultControl() if Control is None else Control
    if not isinstance(ExpectedControl, dict) or set(ExpectedControl) != set(
        DefaultControl()
    ):
        raise ValueError(
            "independent control requires its hash and measured body properties"
        )
    if (
        not isinstance(ExpectedControl["native_sha256"], str)
        or not fullmatch("[0-9a-f]{64}", ExpectedControl["native_sha256"])
        or type(ExpectedControl["body_count"]) is not int
        or ExpectedControl["body_count"] <= 0
        or type(ExpectedControl["volume_mm3"]) not in (int, float)
        or not isfinite(ExpectedControl["volume_mm3"])
        or ExpectedControl["volume_mm3"] <= 0
        or not isinstance(ExpectedControl["center_of_mass_mm"], list)
        or len(ExpectedControl["center_of_mass_mm"]) != 3
        or any(
            type(Value) not in (int, float) or not isfinite(Value)
            for Value in ExpectedControl["center_of_mass_mm"]
        )
    ):
        raise ValueError("independent control requires valid nonzero measured geometry")
    Value = {
        "schema_version": 1,
        "feature": "family:planes:offset-plane",
        "application": "solidworks",
        "application_build": ApplicationBuild,
        "source_pin": SourcePin,
        "options": {"basis": "XY", "direction": 1, "instances": 1, "units": "mm"},
        "prerequisite_feature_types": {
            "SeedProfile": "ProfileFeature",
            "SeedFeature": "Extrusion",
        },
        "cases": Normal,
        "control": ExpectedControl,
        "geometry": {
            "body_count": 1,
            "surface_body_count": 0,
            "volume_mm3": 8000.0,
            "center_of_mass_mm": [20.0, 10.0, 5.0],
            "bounds_mm": [0.0, 0.0, 0.0, 40.0, 20.0, 10.0],
        },
        "plane": {
            "name": "RecipeFeature",
            "type": "RefPlane",
            "normal_world": [0.0, 0.0, 1.0],
            "definition_type": 5,
            "definition_type2": 11,
            "distance_constraint": 8,
            "support_name": "Front Plane",
            "support_type": "RefPlane",
            "units_code": 5,
            "driven_state": 2,
        },
        "tolerances": {
            "linear_mm": 1e-6,
            "volume_mm3": 1e-6,
            "native_metres": 1e-9,
            "relative": 1e-9,
            "normal": 1e-8,
        },
        "verifier_sources": VerifierPins(),
    }
    return {**Value, "expectations_sha256": RecordHash(Value)}
