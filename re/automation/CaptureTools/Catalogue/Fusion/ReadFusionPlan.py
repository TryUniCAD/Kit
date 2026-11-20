# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from hashlib import sha256
from json import loads
from pathlib import Path
from re import fullmatch

from CaptureTools.Catalogue.Fusion.FusionBatch import NormalizeCases
from CaptureTools.Catalogue.Fusion.FusionInputs import (
    KFusionInputs,
    KFusionRoot,
    KFusionScope,
)


# bounded regular reads prevent native handoff paths from changing after source admission
def ReadFusionBytes(Target, Limit=64 * 1024 * 1024):
    if Target.is_symlink() or not Target.is_file():
        raise ValueError("fusion capture requires a regular bounded input")
    with Target.open("rb") as Stream:
        Content = Stream.read(Limit + 1)
    if not 0 < len(Content) <= Limit:
        raise ValueError("fusion capture input is empty or exceeds its byte limit")
    return Content


# prepared evidence must never execute source whose bytes differ from the reviewed plan
def ReadFusionPlan(PlanPath, PlanHash):
    Raw = ReadFusionBytes(PlanPath, 4 * 1024 * 1024)
    if len(Raw) > 4 * 1024 * 1024 or sha256(Raw).hexdigest() != PlanHash:
        raise ValueError("prepared fusion plan changed or exceeds its byte limit")
    Plan = loads(Raw)
    if (
        not isinstance(Plan, dict)
        or set(Plan) != {"schema", "scope", "source_revision", "pins", "cases", "mode"}
        or type(Plan["schema"]) is not int
        or Plan["schema"] != 1
        or Plan["scope"] != KFusionScope
        or not isinstance(Plan["source_revision"], str)
        or not fullmatch("[0-9a-f]{40}", Plan["source_revision"])
    ):
        raise ValueError("invalid parameterized fusion capture plan")
    if NormalizeCases(Plan["cases"], Plan["mode"]) != Plan["cases"]:
        raise ValueError("fusion plan case roster is not canonical")
    if not isinstance(Plan["pins"], dict) or set(Plan["pins"]) != set(KFusionInputs):
        raise ValueError("fusion plan executable dependency roster changed")
    Sources = {}
    for RoleName, Relative in KFusionInputs.items():
        Pin = Plan["pins"][RoleName]
        Target = KFusionRoot / Relative
        if (
            not isinstance(Pin, dict)
            or set(Pin) != {"path", "size_bytes", "sha256"}
            or Pin["path"] != Relative
            or Target.is_symlink()
            or not Target.is_file()
            or not Target.resolve().is_relative_to(KFusionRoot)
        ):
            raise ValueError("fusion plan dependency path changed")
        Content = Target.read_bytes()
        if (
            len(Content) > 64 * 1024 * 1024
            or len(Content) != Pin["size_bytes"]
            or sha256(Content).hexdigest() != Pin["sha256"]
        ):
            raise ValueError(f"fusion capture dependency changed {Relative}")
        Sources[RoleName] = Content
    return Plan, Sources


# sealed helper execution retains its own original file identity and native imports
def LoadFusionTool(Relative, Content):
    Target = KFusionRoot / Path(Relative)
    Namespace = {"__name__": "__kit_catalogue_" + Target.stem, "__file__": str(Target)}
    exec(compile(Content, str(Target), "exec"), Namespace)
    return Namespace
