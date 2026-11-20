# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from hashlib import sha256 as ShaDigest
from json import loads as LoadJson
from math import isfinite as IsFinite
from pathlib import Path
from re import fullmatch as FullMatch


# evidence readers must reject ambiguous objects rather than silently replace duplicate keys
def UniqueObject(Pairs):
    Values = dict(Pairs)
    if len(Values) != len(Pairs):
        raise ValueError("duplicate JSON keys in pilot evidence")
    return Values


# every frozen file keeps the exact bytes supplied by its evidence owner
def ReadObject(FilePath):
    if FilePath.is_symlink() or not FilePath.is_file():
        raise ValueError("pilot evidence must be a regular nonsymlink file")
    Content = FilePath.read_bytes()
    if len(Content) > 16 * 1024 * 1024:
        raise ValueError("pilot evidence file exceeds 16 MiB")
    Record = LoadJson(Content, object_pairs_hook=UniqueObject)
    if not isinstance(Record, dict):
        raise ValueError("pilot evidence must contain an object")
    return Record, ShaDigest(Content).hexdigest()


# actual launch identity and fixed policy must agree before any duration is attributed
def ReadRun(RunRoot):
    Manifest, ManifestHash = ReadObject(RunRoot / "RunManifest.json")
    Observe, ObserveHash = ReadObject(RunRoot / "Observation.json")
    if (
        type(Manifest.get("version")) is not int
        or Manifest["version"] != 1
        or type(Observe.get("version")) is not int
        or Observe["version"] != 1
        or not isinstance(Manifest.get("run_id"), str)
        or not Manifest["run_id"]
        or Observe.get("run_id") != Manifest["run_id"]
        or Observe.get("manifest_sha256") != ManifestHash
        or Manifest.get("model_calls_enabled") is not False
        or Manifest.get("application_dispatch_enabled") is not False
        or Manifest.get("observation_seconds") != 1209600
        or not isinstance(Manifest.get("source_revision"), str)
        or FullMatch("[0-9a-f]{40}", Manifest["source_revision"]) is None
    ):
        raise ValueError("pilot identity or offline policy differs from the launch")
    StartTime = Observe.get("started_at")
    UntilTime = Observe.get("planned_until")
    if (
        type(StartTime) not in (int, float)
        or type(UntilTime) not in (int, float)
        or not IsFinite(StartTime)
        or not IsFinite(UntilTime)
        or StartTime < 0
        or UntilTime - StartTime != 1209600
    ):
        raise ValueError("pilot launch must fix an actual two week observation window")
    return Manifest, Observe, ManifestHash, ObserveHash
