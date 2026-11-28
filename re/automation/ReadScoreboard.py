# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import sys
import time
import unicodedata

sys.path[:0] = [
    str(Path(__file__).resolve().parent),
    str(Path(__file__).resolve().parents[2] / "src"),
]

from Corpus import git
from ReaderEvidence import reader_evidence

# the scoreboard covers every pinned native format that the public reader opens
Formats = {
    "f3d": ("fusion", "fusion.f3d"),
    "f3z": ("fusion", "fusion.f3z"),
    "sldprt": ("solidworks", "solidworks.sldprt"),
    "sldasm": ("solidworks", "solidworks.sldasm"),
}

# every decode reports this marker because independent source inventory is out of reader scope
PermanentReason = "independent_source_inventory_and_native_acceptance_unavailable"

# read options match the census so outcomes stay comparable with the committed baseline
ReadOptions = {"include_brep": True, "include_tessellation": True}

# assemblies need about 5.8 million evidence entries, far above the per-file reader default
EvidenceLimit = 10000000

# the class catalogue names Fusion record GUIDs that the reader leaves as native steps
ClassCatalogue = Path(__file__).resolve().parents[1] / "Fusion/Study/fusion-class-catalog.json"


# observed class semantics give unknown Fusion steps a readable family label
def FusionClassNames():
    if not ClassCatalogue.is_file():
        return {}
    Names = {}
    for Row in json.loads(ClassCatalogue.read_bytes())["classes"]:
        Label = next(
            (Item.split(":", 1)[1].strip() for Item in Row["observed_semantics"] if Item.startswith("Named feature:")),
            None,
        )
        Names[Row["class_guid"].upper()] = Label or "/".join(Row["namespaces"]) + " class " + Row["class_guid"][:8]
    return Names


# a strict read is attempted first and the partial read only records what strict refused
def ReadDocument(Raw, SourceFormat):
    if SourceFormat == "fusion.f3z":
        from FusionReader import read_document

        return read_document(Raw, allow_partial=True)
    from convert import open_document

    try:
        return open_document(Raw, source_format=SourceFormat, strict=True, **ReadOptions), "strict", None
    except ValueError as Error:
        Reason = str(Error)[:1024]
    return open_document(Raw, source_format=SourceFormat, strict=False, **ReadOptions), "partial", Reason


# each feature step is named by its typed definition, native type or native class
def StepLabel(Step, ClassNames):
    Definition = Step.get("definition")
    Attributes = Step.get("attributes") or {}
    if isinstance(Definition, dict) and Definition.get("$type") not in (None, "NativeFeatureDefinition"):
        return Definition["$type"]
    if isinstance(Attributes.get("native_type"), str):
        return Attributes["native_type"]
    Spans = ((Step.get("provenance") or {}).get("spans") or {}).get("$tuple") or []
    Kinds = [Span.get("record_kind") for Span in Spans if isinstance(Span, dict)]
    for Kind in Kinds:
        if isinstance(Kind, str) and Kind.upper() in ClassNames:
            return ClassNames[Kind.upper()]
    if Kinds and isinstance(Kinds[0], str):
        return "class " + Kinds[0][:8]
    Kind = Step.get("kind")
    return "kind " + (Kind.get("value") if isinstance(Kind, dict) else str(Kind))


# unresolved items are attributed to the feature, sketch or document area at their path
def ItemArea(Path, Steps, Labels, Diagnostics):
    Parts = Path.split("/")
    if len(Parts) >= 4 and Parts[1] == "feature_timeline" and Parts[3].isdigit():
        Index = int(Parts[3])
        return "feature: " + (Labels[Index] if Index < len(Steps) else "unknown step")
    if len(Parts) >= 4 and Parts[1] == "diagnostics" and Parts[3].isdigit():
        Index = int(Parts[3])
        Code = Diagnostics[Index].get("code") if Index < len(Diagnostics) else None
        return "diagnostic: " + str(Code)
    if len(Parts) >= 2 and Parts[1]:
        return Parts[1]
    return "document"


# one asset row records its read mode, strict refusal and every unresolved area
def ScoreAsset(Root, Asset, ClassNames):
    Application, SourceFormat = Formats[Asset["format"]]
    Raw = git(Root, "cat-file", "blob", Asset["git_blob"])
    if hashlib.sha256(Raw).hexdigest() != Asset["sha256"]:
        raise ValueError(f"{Asset['path']} differs from its pinned digest")
    Row = {"path": Asset["path"], "application": Application, "format": SourceFormat}
    Started = time.perf_counter()
    try:
        Document, Mode, Reason = ReadDocument(Raw, SourceFormat)
    except ValueError as Error:
        Row.update(outcome="rejected", reason=str(Error)[:1024])
        return Row
    except Exception as Error:
        Row.update(outcome="reader_error", error_type=type(Error).__name__, reason=str(Error)[:1024])
        return Row
    Neutral = json.loads(Document.to_json(indent=None))
    Row["decode_seconds"] = round(time.perf_counter() - Started, 4)
    try:
        Evidence = reader_evidence(Neutral, limit=EvidenceLimit)
    except ValueError as Error:
        Row.update(outcome="evidence_limit", reader_mode=Mode, strict_rejection=Reason, reason=str(Error)[:1024])
        return Row
    Steps = Neutral.get("feature_timeline", {}).get("$tuple", [])
    Diagnostics = Neutral.get("diagnostics", {}).get("$tuple", [])
    Labels = [StepLabel(Step, ClassNames) for Step in Steps]
    Items = [Item for Item in Evidence["unresolved"] if Item["reason"] != PermanentReason]
    Areas = Counter()
    Reasons = Counter()
    for Item in Items:
        Area = ItemArea(Item["path"], Steps, Labels, Diagnostics)
        Areas[Area] += 1
        Reasons[Item["reason"]] += 1
    Row.update(
        outcome="decoded",
        reader_mode=Mode,
        strict_rejection=Reason,
        fully_read=Mode == "strict" and not Items,
        features=dict(Counter(Labels)),
        unresolved=len(Items),
        unresolved_reasons=dict(Reasons),
        unresolved_areas=dict(Areas),
        diagnostics=sorted({str(Item.get("code")) for Item in Diagnostics}),
    )
    return Row


# per-application totals rank the areas that block the most files from a full read
def Summarise(Rows):
    Summary = {}
    for Application in sorted({Row["application"] for Row in Rows}):
        Group = [Row for Row in Rows if Row["application"] == Application]
        Decoded = [Row for Row in Group if Row["outcome"] == "decoded"]
        Areas, AreaItems, Reasons, ReasonItems, Features, Diagnostics, Refusals = (
            Counter(), Counter(), Counter(), Counter(), Counter(), Counter(), Counter()
        )
        for Row in Decoded:
            for Area, Count in Row["unresolved_areas"].items():
                Areas[Area] += 1
                AreaItems[Area] += Count
            for Reason, Count in Row["unresolved_reasons"].items():
                Reasons[Reason] += 1
                ReasonItems[Reason] += Count
            for Label in Row["features"]:
                Features[Label] += 1
            for Code in Row["diagnostics"]:
                Diagnostics[Code] += 1
            if Row["strict_rejection"]:
                Refusals[Row["strict_rejection"].split(":")[0][:160]] += 1
        Summary[Application] = {
            "files": len(Group),
            "strict": sum(Row.get("reader_mode") == "strict" for Row in Decoded),
            "partial": sum(Row.get("reader_mode") == "partial" for Row in Decoded),
            "rejected": sum(Row["outcome"] == "rejected" for Row in Group),
            "reader_error": sum(Row["outcome"] == "reader_error" for Row in Group),
            "evidence_limit": sum(Row["outcome"] == "evidence_limit" for Row in Group),
            "fully_read": sum(Row.get("fully_read", False) for Row in Decoded),
            "unresolved_items": sum(Row["unresolved"] for Row in Decoded),
            "decode_seconds": round(sum(Row.get("decode_seconds", 0) for Row in Decoded), 2),
            "blocking_areas": [
                {"area": Area, "files": Files, "items": AreaItems[Area]} for Area, Files in Areas.most_common()
            ],
            "reasons": [
                {"reason": Reason, "files": Files, "items": ReasonItems[Reason]} for Reason, Files in Reasons.most_common()
            ],
            "strict_refusals": [{"reason": Reason, "files": Files} for Reason, Files in Refusals.most_common()],
            "diagnostics": [{"code": Code, "files": Files} for Code, Files in Diagnostics.most_common()],
            "features_seen": [{"feature": Label, "files": Files} for Label, Files in Features.most_common()],
        }
    return Summary


# the committed census baseline shows where today's Fusion reader moved since it was recorded
def CompareBaseline(Root, Rows):
    Path_ = Root / "re/automation/FusionOutcomes.json"
    if not Path_.is_file():
        return None
    Baseline = {Asset["path"]: Asset for Asset in json.loads(Path_.read_bytes())["assets"]}
    Moves = Counter()
    for Row in Rows:
        Before = Baseline.get(Row["path"])
        if Row["application"] != "fusion" or Before is None:
            continue
        Old = Before.get("reader_mode") or Before["outcome"]
        New = Row.get("reader_mode") or Row["outcome"]
        Moves[f"{Old} -> {New}"] += 1
    return dict(sorted(Moves.items()))


# a short Markdown page lists totals and the top blocking areas per application
def RenderMarkdown(Report, Limit):
    Lines = [
        "# Read scoreboard",
        "",
        f"Source revision `{Report['source_revision']}`, corpus revision `{Report['corpus_revision']}`.",
        "A file is fully read when strict mode accepts it and the reader reports no unresolved item.",
        "Byte ownership is not measured: the reader evidence reports `byte_accounting: unavailable`.",
        "",
        "Read options match the census: B-rep and tessellation payloads are included.",
        "",
        "| Application | Files | Strict | Partial | Rejected | Reader error | Evidence limit | Fully read | Unresolved items |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for Application, Row in Report["summary"].items():
        Lines.append(
            f"| {Application} | {Row['files']} | {Row['strict']} | {Row['partial']} | {Row['rejected']} "
            f"| {Row['reader_error']} | {Row['evidence_limit']} | {Row['fully_read']} | {Row['unresolved_items']} |"
        )
    for Application, Row in Report["summary"].items():
        Lines += ["", f"## {Application}: areas blocking a full read", "", "| Area | Files | Items |", "| --- | ---: | ---: |"]
        Lines += [f"| {Item['area']} | {Item['files']} | {Item['items']} |" for Item in Row["blocking_areas"][:Limit]]
        Lines += ["", f"## {Application}: unresolved reasons", "", "| Reason | Files | Items |", "| --- | ---: | ---: |"]
        Lines += [f"| {Item['reason']} | {Item['files']} | {Item['items']} |" for Item in Row["reasons"][:Limit]]
        Lines += ["", f"## {Application}: strict refusals", "", "| Reason | Files |", "| --- | ---: |"]
        Lines += [f"| {Item['reason']} | {Item['files']} |" for Item in Row["strict_refusals"][:Limit]]
    if Report["fusion_baseline_moves"]:
        Lines += ["", "## Fusion changes since the census baseline", "", "| Baseline -> now | Files |", "| --- | ---: |"]
        Lines += [f"| {Move} | {Count} |" for Move, Count in Report["fusion_baseline_moves"].items()]
    return "\n".join(Lines) + "\n"


# the command scores every pinned native asset or an explicit subset
def Main():
    Parser = argparse.ArgumentParser(description="Score how completely the readers decode every pinned native file")
    Parser.add_argument("--output", type=Path, required=True)
    Parser.add_argument("--asset", action="append", help="limit to these corpus paths")
    Parser.add_argument("--top", type=int, default=25)
    Args = Parser.parse_args()
    Root = Path(__file__).resolve().parents[2]
    if sys.version_info < (3, 14):
        Parser.exit(1, "the Fusion reader needs Python 3.14 for ZIP Zstandard support\n")
    if Args.output.exists():
        Parser.exit(1, "output already exists; choose an unused directory\n")
    Manifest = json.loads((Root / "re/automation/Corpus.json").read_bytes())
    Assets = [Asset for Asset in Manifest["assets"] if Asset.get("kind") == "native" and Asset.get("format") in Formats]
    if Args.asset:
        Wanted = {unicodedata.normalize("NFC", Item) for Item in Args.asset}
        Assets = [Asset for Asset in Assets if unicodedata.normalize("NFC", Asset["path"]) in Wanted]
        if len(Assets) != len(Wanted):
            Parser.exit(1, "every --asset must be a pinned native corpus path\n")
    ClassNames = FusionClassNames()
    Rows = []
    for Index, Asset in enumerate(Assets, 1):
        Rows.append(ScoreAsset(Root, Asset, ClassNames))
        if Index % 50 == 0:
            print(f"scored {Index}/{len(Assets)}", file=sys.stderr, flush=True)
    Report = {
        "scoreboard_version": 1,
        "source_revision": git(Root, "rev-parse", "HEAD").decode("ascii").strip(),
        "corpus_revision": Manifest["source_revision"],
        "read_options": ReadOptions,
        "byte_accounting": "unavailable",
        "summary": Summarise(Rows),
        "fusion_baseline_moves": CompareBaseline(Root, Rows),
        "files": Rows,
    }
    Args.output.mkdir(parents=True)
    (Args.output / "Scoreboard.json").write_text(json.dumps(Report, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    (Args.output / "Scoreboard.md").write_text(RenderMarkdown(Report, Args.top), encoding="utf-8")
    print(json.dumps({Application: {Key: Row[Key] for Key in ("files", "strict", "partial", "rejected", "reader_error", "fully_read")} for Application, Row in Report["summary"].items()}))
    return 0


if __name__ == "__main__":
    raise SystemExit(Main())
