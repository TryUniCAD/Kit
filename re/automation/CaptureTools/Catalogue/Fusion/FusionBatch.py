# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from hashlib import sha256
from json import dumps

from CaptureTools.Catalogue.Fusion.FusionCases import KFusionModes
from CaptureTools.Catalogue.Fusion.FusionParams import ValidateFusion


# generated capture identities must be reproducible without consuming held out lineages
def NormalizeCases(Cases, Mode):
    if not isinstance(Mode, str) or Mode not in KFusionModes:
        raise ValueError(
            "fusion capture mode must be discovery qualification or holdout"
        )
    if not isinstance(Cases, list) or not 1 <= len(Cases) <= 2:
        raise ValueError("a fusion capture batch requires one or two explicit cases")
    Normalized, Identities = [], set()
    for Case in Cases:
        if not isinstance(Case, dict):
            raise ValueError("a fusion capture case must be a record")
        Normal = ValidateFusion(
            {Key: Value for Key, Value in Case.items() if Key != "id"}
        )
        if Normal["recipe"] not in KFusionModes[Mode]:
            raise ValueError("fusion recipe is reserved for another evidence mode")
        Canonical = dumps(
            Normal,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
        Identity = sha256(Canonical).hexdigest()[:16]
        if Case.get("id", Identity) != Identity or Identity in Identities:
            raise ValueError("fusion case identity is changed or duplicated")
        Identities.add(Identity)
        Normalized.append({"id": Identity, **Normal})
    return Normalized


# native measurements consume only normalized model inputs rather than bookkeeping identities
def ModelCase(Case):
    return {Key: Value for Key, Value in Case.items() if Key != "id"}


# both workers must publish the same exact artifact roster before evidence can be accepted
def PhasePaths(Identity, Phase):
    if Phase not in ("a", "b"):
        raise ValueError("fusion capture phase must be a or b")
    Cases = NormalizeCases(Identity["cases"], Identity["mode"])
    Directory = f"phase-{Phase}"
    Files = {
        f"{Directory}.report": f"{Directory}/report.json",
        f"{Directory}.receipt": f"{Directory}/receipt.json",
    }
    for Case in Cases:
        CaseId = Case["id"]
        Files[f"{Directory}.{CaseId}.baseline"] = f"{Directory}/{CaseId}-baseline.f3d"
        if Phase == "b":
            for ParamName in Case["parameters"]:
                Files[f"{Directory}.{CaseId}.edit-{ParamName}"] = (
                    f"{Directory}/{CaseId}-edit-{ParamName}.f3d"
                )
    return Files
