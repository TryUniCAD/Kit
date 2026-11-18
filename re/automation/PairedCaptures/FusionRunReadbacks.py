# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from math import isclose

from PairedCaptures.FusionBindings import CONSTRAINT_TARGETS, DIMENSION_TARGETS


# summary counts must be backed by actual observation local target identities
def CountBindings(Bindings, Binding, TargetKinds, EntityIds):
    Records = Bindings[f"{Binding}s"]
    Unresolved = Bindings[f"unresolved_{Binding}_indices"]
    if not isinstance(Records, list) or not isinstance(Unresolved, list):
        raise ValueError("Fusion sketch binding roster is invalid")
    Gaps = []
    for Index, Record in enumerate(Records):
        Targets = Record["targets"]
        Slots = TargetKinds.get(Record["type"].rsplit("::", 1)[-1])
        if (
            type(Record["index"]) is not int
            or Record["index"] != Index
            or not isinstance(Targets, dict)
            or Targets.keys() != set(Slots or ())
        ):
            raise ValueError("Fusion sketch binding targets do not match the recorded type")
        if Slots is None:
            Status = "unsupported_type"
        else:
            Status = "resolved"
            for Target in Targets.values():
                if Target["status"] != "resolved":
                    Status = "unresolved"
                    continue
                Matches = Target["entity_ids"]
                if not isinstance(Matches, list) or len(Matches) != 1 or Matches[0] not in EntityIds:
                    raise ValueError("Fusion sketch binding does not resolve to an observed entity")
        if Record["binding_status"] != Status:
            raise ValueError("Fusion sketch binding status does not match its targets")
        if Status != "resolved":
            Gaps.append(Index)
    if any(type(Index) is not int for Index in Unresolved) or Unresolved != Gaps:
        raise ValueError("Fusion unresolved binding indices do not match observed targets")
    return len(Records) - len(Gaps), len(Gaps)


# the vendor report must bind each successful observation to the intended archive
def CheckReadback(Reading, InputPin=None, IsBaseline=False):
    if InputPin is not None:
        Imported = Reading["import"]
        if (
            Reading["native_input"] != InputPin
            or Imported["return"] != "document"
            or Imported["exception"] is not None
            or Imported["last_error_on_failure"] is not None
            or Imported["aggregate_loader_warnings"] is not None
            or not Imported["aggregate_loader_warnings_reason"]
        ):
            raise ValueError("Fusion import lacks a successful exact archive observation")
    if Reading["compute_all_return"] is not True:
        raise ValueError("Fusion readback did not complete recompute")
    for Stage in ("before_recompute", "after_recompute"):
        Features = Reading[Stage]["feature_tree"]
        if not Features or any(
            Feature["health"]["state"] != "healthy"
            or Feature["suppressed"] is not False
            or Feature["rolled_back"] is not False
            for Feature in Features
        ):
            raise ValueError("Fusion readback has an unhealthy or missing feature tree")
        if IsBaseline and Reading[f"{Stage}_comparison"]["matches"] is not True:
            raise ValueError("Fusion baseline comparison did not pass")
    Sketches = Reading["after_recompute"]["sketches"]
    if not Sketches:
        raise ValueError("Fusion readback has no sketch observations")
    Counts = {"constraint_bindings": 0, "dimension_bindings": 0, "unresolved_bindings": 0}
    for Sketch in Sketches:
        Bindings = Sketch["bindings"]
        EntityIds = {Record["id"] for Record in Bindings["points"] + Bindings["curves"]}
        for Binding, TargetKinds in (("constraint", CONSTRAINT_TARGETS), ("dimension", DIMENSION_TARGETS)):
            Resolved, Unresolved = CountBindings(Bindings, Binding, TargetKinds, EntityIds)
            Counts[f"{Binding}_bindings"] += Resolved
            Counts["unresolved_bindings"] += Unresolved
    return Counts


# the ordinary control distinguishes a successful document load from an empty session
def CheckControl(Report, ControlPin):
    for Label in ("healthy_control_before", "healthy_control_after"):
        Reading = Report[Label]
        CheckReadback(Reading, ControlPin)
        After = Reading["after_recompute"]
        if After["body_count"] != 1 or not isclose(
            After["volume_mm3"], 30000, rel_tol=1e-9, abs_tol=1e-6
        ):
            raise ValueError("Fusion healthy control failed")


# the old timeline probe cannot establish which face actually supports the sketch
def CountCutSupport(Readings):
    Counts = {"verified_support_faces": 0, "unresolved_support_faces": 0, "verified_cut_participants": 0}
    for Reading in Readings:
        Witness = Reading["cut_reference_evidence"]
        if Witness.get("scope") != "after_normal_recompute":
            if Witness.get("status") != "unresolved":
                raise ValueError("Fusion P04 reference observation has an unknown scope")
            Counts["unresolved_support_faces"] += 1
            continue
        Support = Witness.get("support_before_sketch")
        if Support is not None and "support_after_sketch" in Witness:
            raise ValueError("Fusion P04 has conflicting support probe positions")
        if Support is not None and Support["status"] == "verified":
            if (
                Support["marker"] != 2
                or Support["reference_type"] != "adsk::fusion::BRepFace"
                or Support["boss_end_face_matches"] != 1
                or Support["boss_start_face_matches"] != 0
                or Support["boss_body_matches"] != 1
            ):
                raise ValueError("Fusion P04 support claim does not identify the boss end face")
            Counts["verified_support_faces"] += 1
        else:
            if Support is None:
                Support = Witness["support_after_sketch"]
            if Support["status"] not in ("unavailable", "unresolved"):
                raise ValueError("Fusion P04 support claim has no before-sketch observation")
            Counts["unresolved_support_faces"] += 1
        Parts = Witness["participants_before_cut"]
        if Parts["status"] == "verified":
            if (
                Parts["marker"] != 3
                or Parts["boss_body_count"] != 1
                or Parts["participant_count"] != 1
                or Parts["boss_body_matches_per_participant"] != [1]
            ):
                raise ValueError("Fusion P04 participant claim does not identify the boss body")
            Counts["verified_cut_participants"] += 1
        elif Parts["status"] not in ("unavailable", "unresolved"):
            raise ValueError("Fusion P04 participant status is invalid")
    return Counts


# the plan must account for both repeat saves and every historical archive in the recipe
def CheckRecipeRead(Recipe, First, Repeat, Historical):
    Prior = Historical["archives"]
    if (
        Repeat["existing_source_receipt"] != Historical["receipt"]
        or Repeat["existing_source_measurements"] != Historical["measurements"]
        or Repeat["existing_variant_readbacks"].keys() != Historical["variants"].keys()
    ):
        raise ValueError(f"{Recipe} Fusion historical readback roster differs from its plan")
    CheckReadback(First, IsBaseline=True)
    Fresh = [
        (Repeat["fresh_reopen_a"], First["save_a"]),
        (Repeat["repeat_readback_b"], Repeat["save_b"]),
    ]
    Originals = [
        (Repeat["existing_readback_a"], Prior["a"], True),
        (Repeat["existing_readback_b"], Prior["b"], True),
    ]
    Originals.extend(
        (Repeat["existing_variant_readbacks"][Name], PinValue, False)
        for Name, PinValue in Historical["variants"].items()
    )
    for Reading, InputPin in Fresh:
        CheckReadback(Reading, InputPin, IsBaseline=True)
    Result = {
        "fresh_readbacks": len(Fresh),
        "historical_readbacks": len(Originals),
        "historical_constraint_bindings": 0,
        "historical_dimension_bindings": 0,
        "historical_unresolved_bindings": 0,
        "fresh_archives": [First["save_a"], Repeat["save_b"]],
    }
    for Reading, InputPin, IsBaseline in Originals:
        for Name, Count in CheckReadback(Reading, InputPin, IsBaseline).items():
            Result[f"historical_{Name}"] += Count
    if Recipe == "P04":
        Result.update(CountCutSupport([First, *(Item[0] for Item in Fresh + Originals)]))
    return Result
