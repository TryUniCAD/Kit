# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from struct import pack_into as PackInto

from convert.adapters.solidworks.Config.RootLayout import KConfigGen
from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive
from convert.adapters.solidworks.Resolved.Circular.ReadCircleOnly import ReadCircleOnly
from tests.Convert.Solidworks.Core.CircleOnly.Samples import KRepoRoot, ReadCircleInput


# adversarial archives locate edited fields through typed records rather than captured byte positions
def AlterCircle(ModeValue: str) -> bytes:
    SourceBytes = ReadCircleInput("baseline-a")
    Archive = SldprtArchive.from_bytes(SourceBytes)
    Streams = Archive.streams
    Stream = "Contents/Config-0-ResolvedFeatures"
    if ModeValue in {"body", "history"}:
        SolidPath = (
            KRepoRoot
            / "re/automation/PairedCaptures/P03/solidworks-db1390476325/P03-solidworks-baseline-a.SLDPRT"
        )
        SolidArchive = SldprtArchive.from_bytes(SolidPath.read_bytes())
        TargetStream = "Contents/Config-0-Partition" if ModeValue == "body" else Stream
        Streams[TargetStream] = SolidArchive.streams[TargetStream]
        return BuildSldprt(Streams, Template=SourceBytes)
    Parsed = ReadCircleOnly(Streams["Contents/Config-0"], Streams[Stream], KConfigGen)
    Changed = bytearray(Streams[Stream])
    if ModeValue == "diameter":
        PackInto("<d", Changed, Parsed.Diameter["parameter_offset"], 0.016)
    elif ModeValue == "support":
        PackInto("<i", Changed, Parsed.Reference.FeatureOffset, 3)
    elif ModeValue == "flags":
        PackInto("<H", Changed, Parsed.Support["span"][1], 2)
    elif ModeValue == "footer":
        PackInto("<i", Changed, Parsed.EndOffset - 4, 1)
    else:
        raise ValueError("unknown source mutation")
    Streams[Stream] = bytes(Changed)
    return BuildSldprt(Streams, Template=SourceBytes)
