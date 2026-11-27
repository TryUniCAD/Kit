from gzip import decompress as UnpackBytes
from hashlib import sha256 as DigestBytes
from json import dumps as EncodeJson, loads as ParseJson
from pathlib import Path as FilePath

from tests.Research.Archives.Comparison.BulkProcess import KRepoRoot


# historical export custody must survive extraction before the actual comparator evaluates the unchanged document fields
def WriteExportMut(
    ExportPath: FilePath,
    CaseName: str,
    FormatName: str,
    OriginalPins: dict[FilePath, str],
) -> dict[str, str]:
    LadderRoot = KRepoRoot / "re/FeatureLadders2026"
    LedgerPath = LadderRoot / "Manifest.json"
    LedgerBytes = LedgerPath.read_bytes()
    OriginalPins[LedgerPath] = DigestBytes(LedgerBytes).hexdigest()
    LadderLedger = ParseJson(LedgerBytes)
    ReportName = f"Reports/{CaseName}/control-before-neutral.json.gz"
    CaseEntry = next(
        Entry for Entry in LadderLedger["cases"] if Entry["case"]["id"] == CaseName
    )
    DecodeEntry = next(
        Entry for Entry in CaseEntry["decodes"] if Entry["neutral_report"] == ReportName
    )
    Artifact = next(
        Entry for Entry in LadderLedger["artifacts"] if Entry["path"] == ReportName
    )
    SourcePath = LadderRoot / ReportName
    PackedBytes = SourcePath.read_bytes()
    OriginalPins[SourcePath] = DigestBytes(PackedBytes).hexdigest()
    assert (OriginalPins[SourcePath], len(PackedBytes)) == (
        Artifact["sha256"],
        Artifact["size_bytes"],
    )
    NativePath = LadderRoot / DecodeEntry["native_path"]
    OriginalPins[NativePath] = DigestBytes(NativePath.read_bytes()).hexdigest()
    Envelope = ParseJson(UnpackBytes(PackedBytes))
    assert (
        DecodeEntry["outcome"],
        DecodeEntry["semantic_qualification"],
        Envelope["kind"],
        Envelope["layer"],
        Envelope["partial"],
    ) == ("strict_decoded", "unverified", "kit.decode", "neutral", False)
    Document = Envelope["document"]
    Source = Document["source"]
    assert (
        Document["$type"],
        Document["units"],
        Source["format_id"],
        Source["sha256"],
        OriginalPins[NativePath],
    ) == (
        "CadDocument",
        {"$enum": "UnitSystem", "value": "mm"},
        FormatName,
        DecodeEntry["source_sha256"],
        DecodeEntry["source_sha256"],
    )
    assert Document["metadata"]
    ExportBytes = EncodeJson(
        Document, sort_keys=True, ensure_ascii=False, allow_nan=False
    ).encode("utf-8")
    assert ExportPath.write_bytes(ExportBytes) == len(ExportBytes)
    OriginalPins[ExportPath] = DigestBytes(ExportBytes).hexdigest()
    return {
        "input_sha256": OriginalPins[ExportPath],
        "source_sha256": Source["sha256"],
        "source_identity_sha256": DigestBytes(
            EncodeJson(Source, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest(),
    }
