# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from copy import deepcopy
from math import isfinite
from re import fullmatch
from secrets import choice, token_hex

from InferenceGrid.BuilderDevelopment.Verification.FreezeExpectations import RecordHash


# qualification observations exposed during repair may never be reused to evaluate a revision
def ReserveQualification(History, ForbiddenValues, Count=3):
    if not isinstance(History, list) or type(Count) is not int or not 1 <= Count <= 3:
        raise ValueError(
            "qualification requires bounded reservation history and case count"
        )
    Used = set()
    for Value in ForbiddenValues:
        if type(Value) not in (int, float) or not isfinite(Value):
            raise ValueError("discovery exclusions must be finite numbers")
        Used.add(float(Value))
    for Reservation in History:
        CheckReservation(Reservation)
        for Case in Reservation["cases"]:
            Used.update((Case["offset_mm"], Case["edit_mm"]))
    Pool = [
        Value / 4
        for Value in range(8, 240)
        if Value / 4 not in Used and Value / 4 + 0.125 not in Used
    ]
    if len(Pool) < Count:
        raise ValueError("independent qualification reserve exhausted")
    Identity = token_hex(12)
    Cases = []
    for Index in range(Count):
        Value = choice(Pool)
        Pool.remove(Value)
        Cases.append(
            {
                "id": f"q-{Identity}-{Index + 1}",
                "offset_mm": Value,
                "edit_mm": Value + 0.125,
            }
        )
    return {
        "schema_version": 1,
        "id": Identity,
        "cases": Cases,
        "cases_sha256": RecordHash(Cases),
        "status": "reserved",
        "candidate_sha256": None,
        "diagnostics_exposed": False,
    }


# a case hash detects altered hidden values before candidate freezing or retirement
def CheckReservation(Reservation):
    if (
        not isinstance(Reservation, dict)
        or Reservation.get("schema_version") != 1
        or not isinstance(Reservation.get("cases"), list)
    ):
        raise ValueError("invalid qualification reservation")
    if RecordHash(Reservation["cases"]) != Reservation.get("cases_sha256"):
        raise ValueError("qualification reservation cases changed")
    if Reservation.get("status") not in {"reserved", "frozen", "retired"}:
        raise ValueError("invalid qualification reservation state")


# the immutable candidate digest is fixed before the native qualification session sees its cases
def FreezeQualification(Reservation, CandidateSha256):
    CheckReservation(Reservation)
    if (
        Reservation["status"] != "reserved"
        or Reservation.get("candidate_sha256") is not None
    ):
        raise ValueError("qualification reservation was already frozen or consumed")
    if not isinstance(CandidateSha256, str) or not fullmatch(
        "[0-9a-f]{64}", CandidateSha256
    ):
        raise ValueError("qualification requires a frozen candidate digest")
    return {
        **deepcopy(Reservation),
        "status": "frozen",
        "candidate_sha256": CandidateSha256,
    }


# failed or exposed qualification cases remain permanently retired in the development journal
def RetireQualification(Reservation, DiagnosticsExposed=True):
    CheckReservation(Reservation)
    if Reservation["status"] != "frozen" or type(DiagnosticsExposed) is not bool:
        raise ValueError("only a frozen qualification reservation can be retired")
    return {
        **deepcopy(Reservation),
        "status": "retired",
        "diagnostics_exposed": DiagnosticsExposed,
    }
