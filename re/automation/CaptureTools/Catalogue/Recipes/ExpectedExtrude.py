# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from math import pi


# independent prism and seed moments expose wrong starts directions extents and up to references
def ExpectedExtrude(Program, Direction):
    Profile, Operation = Program["profile"], Program["operation"]
    Start, End = Operation["start"], Operation["end"]
    Offset = -Start["offset_mm"] if Start["reverse"] else Start["offset_mm"]
    OriginU, OriginV, OriginN = Profile["origin_mm"]
    OriginN += Offset
    if End["kind"] == "up_to_plane":
        Seed = Program["seed"]
        Height = End["target_z_mm"] - OriginN
        Added = pi * (Profile["diameter_mm"] / 2) ** 2 * Height
        SeedVolume = Seed["width_mm"] * Seed["depth_mm"] * Seed["height_mm"]
        Volume = SeedVolume + Added
        Center = [
            (SeedVolume * Seed["width_mm"] / 2 + Added * OriginU) / Volume,
            (SeedVolume * Seed["depth_mm"] / 2 + Added * OriginV) / Volume,
            (
                SeedVolume * Seed["height_mm"] / 2
                + Added * (OriginN + End["target_z_mm"]) / 2
            )
            / Volume,
        ]
        return {
            "body_count": 1,
            "volume_mm3": Volume,
            "center_of_mass_mm": Center,
            "bounds_mm": [
                [0.0, 0.0, 0.0],
                [Seed["width_mm"], Seed["depth_mm"], End["target_z_mm"]],
            ],
        }
    if End["kind"] == "midplane":
        LowerN, UpperN = OriginN - End["depth1_mm"] / 2, OriginN + End["depth1_mm"] / 2
    elif End["kind"] == "two_direction":
        LowerN, UpperN = sorted(
            (
                OriginN - Direction * End["depth2_mm"],
                OriginN + Direction * End["depth1_mm"],
            )
        )
    else:
        LowerN, UpperN = sorted((OriginN, OriginN + Direction * End["depth1_mm"]))
    if Profile["kind"] == "rectangle":
        Width, Height = Profile["width_mm"], Profile["height_mm"]
        LowerV = OriginV
    else:
        Width, Height = Profile["length_mm"], Operation["thin"]["thickness_mm"]
        LowerV = (
            OriginV - Height / 2 if Operation["thin"]["side"] == "midplane" else OriginV
        )
    return {
        "body_count": 1,
        "volume_mm3": Width * Height * (UpperN - LowerN),
        "center_of_mass_mm": [
            OriginU + Width / 2,
            LowerV + Height / 2,
            (LowerN + UpperN) / 2,
        ],
        "bounds_mm": [
            [OriginU, LowerV, LowerN],
            [OriginU + Width, LowerV + Height, UpperN],
        ],
    }
