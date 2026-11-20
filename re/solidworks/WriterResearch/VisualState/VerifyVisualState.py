# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from argparse import ArgumentParser
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "re/solidworks/WriterResearch")]

from CmgrBossMass import CalcBossMass
from OrdinaryConfig import BuildOrdinaryConfig
from OrdinaryPackage import BuildOrdinaryPackage, KConfigManager
from PartFraming import KPartGeneration
from ResolvedPart import BuildOrdinaryResolved
from VerifyFreshBoss import (
    BuildPackageState,
    FixtureState,
    ParseContext,
    PublishCandidate,
    VerifyFreshBoss,
)
from VisualState.VerifyAuthoredAppearance import BindDocumentColor, CheckInlineAppearances
from VisualState.VisualStateArchive import EncodeVisualState
from VisualState.VisualStateModel import CanonicalState, KVisualStateMember
from VisualState.VisualStatePackage import MakePackageVisuals
from VisualState.VisualStateReadback import DecodeVisualState
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.Format import KConfigStream


def VerifyCorpus():
    from VerifyConfigRoot import CAPTURE_REVISION, principal_captures

    Rows = []
    for _, Asset, Data, _, _ in principal_captures():
        if "/P03/" not in Asset["path"]:
            continue
        Archive = SldprtArchive.from_bytes(Data)
        Source = Archive.require(KVisualStateMember)
        State = DecodeVisualState(Source, KPartGeneration)
        RequireArch(
            EncodeVisualState(KPartGeneration, State),
            Source,
            "exact sealed control roundtrip",
        )
        Rows.append(
            {
                "path": Asset["path"],
                "bytes": len(Source),
                "sha256": sha256(Source).hexdigest(),
                "owners": len(State.Owners),
            }
        )
    RequireArch(len(Rows), 8, "all eight sealed principal controls")
    return {
        "capture_revision": CAPTURE_REVISION,
        "controls": Rows,
        "native_acceptance": False,
    }


# independent construction must preserve every member unrelated to the requested visual change
def VerifyAuthored(Context, Settings, Candidate):
    Required = {"representation_id", "name", "visibility"}
    RequireArch(
        type(Settings) is dict
        and Required <= set(Settings) <= Required | {"document_rgb"},
        True,
        "explicit authored visual settings",
    )
    Baseline = VerifyFreshBoss(Context)
    Bound, Owners, Metadata = FixtureState(Context)
    Config = BuildOrdinaryConfig(KPartGeneration, Owners.Config)
    Resolved = BuildOrdinaryResolved(
        KPartGeneration, Config, Owners.System, Bound.Profile, Bound.Boss
    )
    Mass = CalcBossMass(
        Bound.Bounds.Minimum, Bound.Bounds.Maximum, Owners.Config.First.DensityKgM3
    )
    Package = BuildPackageState(Context, Owners, Metadata, Mass)
    Plain = BuildOrdinaryPackage(
        KPartGeneration,
        Owners.Config,
        Config,
        Resolved,
        Bound.Profile,
        Bound.Boss,
        Package,
    )
    RequireArch(
        sha256(Plain).hexdigest(),
        Baseline["archive_sha256"],
        "unchanged default package generation",
    )
    Configuration = Owners.Config
    HasDocumentColor = "document_rgb" in Settings
    if HasDocumentColor:
        Configuration, Package = BindDocumentColor(
            Configuration, Package, Settings["document_rgb"]
        )
        Config = BuildOrdinaryConfig(KPartGeneration, Configuration)
        Resolved = BuildOrdinaryResolved(
            KPartGeneration, Config, Owners.System, Bound.Profile, Bound.Boss
        )
    Visual = MakePackageVisuals(
        Package,
        Bound.Profile,
        Owners.System,
        Settings["representation_id"],
        Settings["name"],
        Settings["visibility"],
    )
    Data = BuildOrdinaryPackage(
        KPartGeneration,
        Configuration,
        Config,
        Resolved,
        Bound.Profile,
        Bound.Boss,
        replace(Package, Visualization=Visual),
    )
    Archive, Original = SldprtArchive.from_bytes(Data), SldprtArchive.from_bytes(Plain)
    RequireArch(
        KVisualStateMember not in Original.streams,
        True,
        "legacy package has no optional visual member",
    )
    RequireArch(
        set(Archive.streams),
        {*Original.streams, KVisualStateMember},
        "one explicit visual member added",
    )
    InlineMembers = {KConfigManager, KConfigStream} if HasDocumentColor else set()
    for Name in set(Original.streams) - InlineMembers:
        RequireArch(
            Archive.require(Name),
            Original.require(Name),
            "unchanged geometry and package metadata",
        )
    if HasDocumentColor:
        CheckInlineAppearances(Archive, Original, KPartGeneration, Package.Manager.Visual)
    Payload = Archive.require(KVisualStateMember)
    Saved = DecodeVisualState(Payload, KPartGeneration)
    RequireArch(
        Saved, CanonicalState(Visual), "authored complete visual state readback"
    )
    if Candidate is not None:
        PublishCandidate(Candidate, Data)
    return {
        **Baseline,
        "archive_sha256": sha256(Data).hexdigest(),
        "stream_count": len(Archive.streams),
        "visual_state": {
            "name": Saved.Name,
            "representation_id": Saved.RepresentationId,
            "appearance_id": Saved.Owners[0].Material.AppearanceId,
            **({"document_rgb": Settings["document_rgb"]} if HasDocumentColor else {}),
            "visibility": {
                (
                    "holder" if Owner.FeatureId is None else str(Owner.FeatureId)
                ): Owner.Display.Visible
                for Owner in Saved.Owners
            },
            "feature_clocks": {
                str(Owner.FeatureId): Owner.Created
                for Owner in Saved.Owners
                if Owner.FeatureId is not None
            },
            "member_sha256": sha256(Payload).hexdigest(),
            "bytes": len(Payload),
        },
        "native_acceptance": False,
    }


def Main():
    Parser = ArgumentParser(
        description="Construct and reread explicit standalone generation 19000 visual states"
    )
    Mode = Parser.add_mutually_exclusive_group(required=True)
    Mode.add_argument("--replay-corpus", action="store_true")
    Mode.add_argument("--fixture-context", type=str)
    Parser.add_argument("--visual-state", type=str)
    Parser.add_argument("--candidate", type=Path)
    Args = Parser.parse_args()
    try:
        if Args.replay_corpus:
            RequireArch(
                (Args.visual_state, Args.candidate),
                (None, None),
                "corpus verification has no candidate inputs",
            )
            Report = VerifyCorpus()
        else:
            RequireArch(
                Args.visual_state is not None,
                True,
                "caller supplies complete visual settings",
            )
            Text = (
                sys.stdin.read()
                if Args.fixture_context == "-"
                else Path(Args.fixture_context).read_text(encoding="utf-8")
            )
            Report = VerifyAuthored(
                ParseContext(Text), json.loads(Args.visual_state), Args.candidate
            )
    except (OSError, ValueError, TypeError, KeyError) as Error:
        Parser.exit(1, f"visual-state verification failed: {Error}\n")
    print(json.dumps(Report, sort_keys=True))


if __name__ == "__main__":
    Main()
