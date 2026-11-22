# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from math import isfinite
from pathlib import Path
from re import fullmatch

from Corpus import git
from InferenceGrid.Authoring.SolidSources import ReadSolidPins


# bounded operations are code generation input rather than arbitrary executable source
def CheckPlaneProgram(Program):
    if (
        not isinstance(Program, dict)
        or set(Program) != {"schema", "operation", "support", "scale", "reverse"}
        or type(Program["schema"]) is not int
        or Program["schema"] != 1
        or Program["operation"] not in ("offset_plane", "coincident_plane")
        or Program["support"] not in ("XY", "YZ", "XZ")
        or type(Program["scale"]) not in (int, float)
        or not isfinite(Program["scale"])
        or not -2 <= Program["scale"] <= 2
        or type(Program["reverse"]) is not bool
    ):
        raise ValueError("candidate is not a bounded native plane program")
    return dict(Program)


# archived generated source makes the bounded program's actual native calls reviewable
def PlaneSource(Program):
    Program = CheckPlaneProgram(Program)
    Support = {"XY": "Front Plane", "YZ": "Right Plane", "XZ": "Top Plane"}[
        Program["support"]
    ]
    if Program["operation"] == "coincident_plane":
        Call = "var feature = document.FeatureManager.InsertRefPlane(4, 0, 0, 0, 0, 0) as SolidWorks.Interop.sldworks.IFeature;"
    else:
        Call = (
            f"double distance = {float(Program['scale'])!r} * offset_mm * 0.001;\n"
            f"bool reverse = {str(Program['reverse']).lower()} ^ (distance < 0);\n"
            "var feature = document.FeatureManager.InsertRefPlane(8 | (reverse ? 256 : 0), System.Math.Abs(distance), 0, 0, 0, 0) as SolidWorks.Interop.sldworks.IFeature;"
        )
    return (
        "// SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0\n"
        "// SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin\n//\n"
        "// This SPDX license identifier and copyright notice must not be\n"
        "// removed, altered, or obscured. Doing so is a material breach of\n"
        "// the PolyForm Strict License 1.0.0 and voids all licenses granted\n"
        "// to you under it immediately and permanently.\n\n"
        "public static class GeneratedPlaneBuilder {\n"
        "    public static SolidWorks.Interop.sldworks.IFeature BuildCandidate(SolidWorks.Interop.sldworks.IModelDoc2 document, double offset_mm) {\n"
        "        document.ClearSelection2(true);\n"
        f'        if (!document.Extension.SelectByID2("{Support}", "PLANE", 0, 0, 0, false, 0, null, 0))\n'
        '            throw new System.InvalidOperationException("Candidate support selection failed");\n'
        + "\n".join("        " + Line for Line in Call.splitlines())
        + '\n        if (feature == null) throw new System.InvalidOperationException("Candidate plane creation failed");\n'
        "        return feature;\n    }\n}\n"
    )


# immutable source evidence includes every legacy helper and each new collector dependency
def PlaneSourcePins(SourceRoot):
    Revision = git(SourceRoot, "rev-parse", "HEAD").decode("ascii").strip()
    Pins = ReadSolidPins(Revision, SourceRoot)
    Known = {Item["path"] for Item in Pins}
    Directory = Path(__file__).resolve().parent
    from hashlib import sha256

    Tracked = (
        git(
            SourceRoot,
            "ls-tree",
            "-r",
            "--name-only",
            Revision,
            "--",
            Directory.relative_to(SourceRoot).as_posix(),
        )
        .decode("utf-8")
        .splitlines()
    )
    Sources = (
        list(Directory.iterdir())
        + [SourceRoot / Relative for Relative in Tracked]
        + [
            SourceRoot / Relative
            for Relative in (
                "re/automation/WindowsProcess.py",
                "re/automation/WindowsApi.py",
                "re/automation/WindowsJobMembers.py",
                "re/automation/ApplicationWorkers/WindowsIdentity.py",
            )
        ]
    )
    for Source in sorted(set(Sources)):
        if Source.suffix not in {".py", ".cs", ".ps1"}:
            continue
        Relative = Source.relative_to(SourceRoot).as_posix()
        if Source.is_symlink() or not Source.is_file():
            raise ValueError("native plane source must be a regular file")
        Content = Source.read_bytes()
        if Content != git(SourceRoot, "show", Revision + ":" + Relative):
            raise ValueError("native plane source differs from its committed revision")
        if Relative not in Known:
            Pins.append(
                {
                    "path": Relative,
                    "sha256": sha256(Content).hexdigest(),
                    "size_bytes": len(Content),
                }
            )
    return Revision, sorted(Pins, key=lambda Item: Item["path"])


# reserved case identities and values enter the native worker without acceptance expectations
def PlaneCases(Cases):
    if not isinstance(Cases, list) or not 1 <= len(Cases) <= 3:
        raise ValueError("native plane execution requires one to three cases")
    Seen = set()
    for Case in Cases:
        if (
            not isinstance(Case, dict)
            or set(Case) != {"id", "offset_mm", "edit_mm"}
            or not isinstance(Case["id"], str)
            or fullmatch(r"[A-Za-z0-9_-]{1,40}", Case["id"]) is None
            or Case["id"] in Seen
        ):
            raise ValueError("invalid native plane case identity")
        Seen.add(Case["id"])
        for Name in ("offset_mm", "edit_mm"):
            if (
                type(Case[Name]) not in (int, float)
                or not isfinite(Case[Name])
                or not 0 < Case[Name] <= 1000
            ):
                raise ValueError("native plane case requires finite positive controls")
        if Case["offset_mm"] == Case["edit_mm"]:
            raise ValueError("native plane edit must differ from its baseline")
    return Cases
