# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from re import fullmatch

from Corpus import git
from InferenceGrid.Authoring.NativeSources import KSourceFiles
from InferenceInputs import checksum, parse_metadata
from Records import digest

KChecklist = "re/CatalogueChecklist"
KEntryLimit = 8192
KCaptureKinds = {"capture.catalogue.solidworks", "capture.catalogue.solidworks.batch"}
KAuthoring = "re/automation/InferenceGrid/Authoring/"
KCapturePaths = (
    *KSourceFiles,
    "re/automation/CaptureTools",
    *(
        KAuthoring + Name + ".py"
        for Name in (
            "SolidWorker",
            "SolidBatchWorker",
            "SolidSources",
            "NativeSources",
            "PackNative",
            "NativeAttempt",
            "NativeEnvironment",
        )
    ),
)
KReaderPaths = (
    "src",
    "pyproject.toml",
    "uv.lock",
    KAuthoring + "DecodeCapture.py",
    KAuthoring + "DecodeWorker.py",
    KAuthoring + "ReadNative.py",
    "re/automation/ReaderEvidence.py",
)


# git tree identities let documentation and checklist commits preserve earlier results
def ChecklistFingerprints(Root, Revision):
    if not isinstance(Revision, str) or not fullmatch("[0-9a-f]{40}", Revision):
        raise ValueError("checklist source revision must be a full Git commit SHA")
    Capture = git(Root, "ls-tree", "-z", Revision, "--", *KCapturePaths)
    Reader = git(Root, "ls-tree", "-z", Revision, "--", *KReaderPaths)
    return digest(["capture@1", Capture.hex()]), digest(["decoder@1", Reader.hex()])


def CaseBody(Plan, Identity):
    return {
        Key: Value
        for Key, Value in Plan["samples"][Identity]["case"].items()
        if Key != "id"
    }


def CaseKey(Plan, Identity):
    return digest(["solidworks", Plan["mode"], CaseBody(Plan, Identity)])


def CheckEntry(Entry):
    if (
        set(Entry) != {"version", "case", "capture", "decode"}
        or type(Entry["version"]) is not int
        or Entry["version"] != 1
    ):
        raise ValueError("invalid catalogue checklist entry")
    checksum(Entry["case"])
    Capture = Entry["capture"]
    if not isinstance(Capture, dict) or set(Capture) != {
        "fingerprint",
        "revision",
        "receipt",
        "bundle",
        "role",
        "report",
    }:
        raise ValueError("invalid catalogue checklist capture")
    CheckRevisionPin(Capture["revision"])
    for Key in ("fingerprint", "receipt", "bundle", "report"):
        checksum(Capture[Key])
    if not isinstance(Capture["role"], str) or not fullmatch(
        r"bundle(?:\.[012])?", Capture["role"]
    ):
        raise ValueError("invalid catalogue checklist bundle role")
    Decode = Entry["decode"]
    if Decode is None:
        return
    if not isinstance(Decode, dict) or set(Decode) != {
        "fingerprint",
        "revision",
        "receipt",
        "status",
        "files",
        "unresolved",
        "unsupported",
    }:
        raise ValueError("invalid catalogue checklist decoder report")
    CheckRevisionPin(Decode["revision"])
    checksum(Decode["fingerprint"])
    checksum(Decode["receipt"])
    if (
        Decode["status"] not in ("read", "decode_unresolved")
        or type(Decode["files"]) is not int
        or not 1 <= Decode["files"] <= 48
        or any(
            type(Decode[Key]) is not int or Decode[Key] < 0
            for Key in ("unresolved", "unsupported")
        )
        or Decode["unsupported"] > Decode["files"]
        or (Decode["status"] == "read")
        != (Decode["unresolved"] == Decode["unsupported"] == 0)
    ):
        raise ValueError("invalid catalogue checklist decoder outcome")


def CheckRevisionPin(Revision):
    if not isinstance(Revision, str) or not fullmatch("[0-9a-f]{40}", Revision):
        raise ValueError("checklist source revision must be a full Git commit SHA")


# one bounded batch reads only committed entries for selected cases
def ReadEntries(Root, Revision, Keys):
    if not Keys:
        return []
    Tree = git(Root, "ls-tree", "-rlz", Revision, "--", KChecklist)
    Rows = []
    for Line in Tree.split(b"\0"):
        if not Line:
            continue
        Metadata, Path = Line.split(b"\t", 1)
        Parts = Path.split(b"/")
        if len(Parts) != 4 or Parts[2].decode("ascii", "replace") not in Keys:
            continue
        Mode, Kind, Object, Size = Metadata.split()
        if Mode != b"100644" or Kind != b"blob" or not 1 <= int(Size) <= KEntryLimit:
            raise ValueError(
                "catalogue checklist entries must be small regular Git blobs"
            )
        Rows.append((Path.decode("ascii"), Object, int(Size)))
    if not Rows:
        return []
    Entries = []
    for Start in range(0, len(Rows), 128):
        Entries.extend(ReadEntryBatch(Root, Rows[Start : Start + 128]))
    return Entries


def ReadEntryBatch(Root, Rows):
    Output = git(
        Root,
        "cat-file",
        "--batch",
        input_data=b"\n".join(Row[1] for Row in Rows) + b"\n",
    )
    Entries, Offset = [], 0
    for Path, Object, Size in Rows:
        Header = Object + b" blob " + str(Size).encode("ascii") + b"\n"
        if not Output.startswith(Header, Offset):
            raise ValueError("invalid catalogue checklist Git blob")
        Offset += len(Header)
        if Output[Offset + Size : Offset + Size + 1] != b"\n":
            raise ValueError("truncated catalogue checklist Git blob")
        Entry = parse_metadata(Output[Offset : Offset + Size])
        Offset += Size + 1
        CheckEntry(Entry)
        if Path != EntryPath(Entry):
            raise ValueError(
                "catalogue checklist entry differs from its content address"
            )
        Entries.append(Entry)
    return Entries


def EntryPath(Entry):
    return f"{KChecklist}/{Entry['case']}/{digest(Entry)}.json"
