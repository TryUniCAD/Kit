from hashlib import sha256 as HashContent
from json import dumps as EncodeJson, loads as DecodeJson
from pathlib import Path as FilePath

from tests.CliResearch.ResearchClient import ResearchCli

# independent identity reconstruction prevents custody hashes from hiding a semantically rebound neutral source
KIdentityFields = (
    "schema",
    "application",
    "sdk_revision",
    "sdk_sources_sha256",
    "runtime",
    "source_sha256",
    "neutral_sha256",
    "candidate_sha256",
    "edit",
    "written_at",
    "native_locators",
)


# receipt ingress must reject changed neutral source identity even when every custody hash is recomputed
def VerifySourcePin(
    TmpPath: FilePath, OutputPath: FilePath, ReceiptPath: FilePath
) -> None:
    Original = {Entry.name: Entry.read_bytes() for Entry in OutputPath.iterdir()}
    assert (
        DecodeJson(Original["document.json"])["source"]["format_id"]
        == "solidworks.sldprt"
    )
    for CaseName, FieldName, FieldValue in (
        ("Format", "format_id", "fusion.f3d"),
        ("Digest", "sha256", "0" * 64),
    ):
        TamperedPath = TmpPath / ("TamperedSource" + CaseName)
        TamperedPath.mkdir()
        for FileName, Content in Original.items():
            _ = (TamperedPath / FileName).write_bytes(Content)
        Document = DecodeJson(Original["document.json"])
        Document["source"][FieldName] = FieldValue
        NeutralBytes = (
            EncodeJson(
                Document,
                sort_keys=True,
                ensure_ascii=False,
                allow_nan=False,
                separators=(",", ":"),
            )
            + "\n"
        ).encode("utf-8")
        _ = (TamperedPath / "document.json").write_bytes(NeutralBytes)
        Manifest = DecodeJson(Original["manifest.json"])
        NeutralHash = HashContent(NeutralBytes).hexdigest()
        Manifest["neutral_sha256"] = NeutralHash
        Manifest["source"]["neutral"].update(
            {"sha256": NeutralHash, "bytes": len(NeutralBytes)}
        )
        Identity = {FieldName: Manifest[FieldName] for FieldName in KIdentityFields}
        IdentityBytes = (
            EncodeJson(
                Identity,
                sort_keys=True,
                ensure_ascii=False,
                allow_nan=False,
                separators=(",", ":"),
            )
            + "\n"
        ).encode("utf-8")
        Manifest["run_fingerprint"] = HashContent(IdentityBytes).hexdigest()
        _ = (TamperedPath / "manifest.json").write_text(
            EncodeJson(
                Manifest,
                sort_keys=True,
                ensure_ascii=False,
                allow_nan=False,
                separators=(",", ":"),
            )
            + "\n",
            encoding="utf-8",
            newline="\n",
        )
        Snapshot = {Entry.name: Entry.read_bytes() for Entry in TamperedPath.iterdir()}
        Result = ResearchCli(
            TmpPath,
            "encoder-round-trip",
            "attach-receipt",
            "--output",
            str(TamperedPath),
            "--role",
            "edited",
            "--receipt",
            str(ReceiptPath),
        )
        assert Result.returncode == 1, Result.stdout + Result.stderr
        assert (
            DecodeJson(Result.stderr)["error"]
            == "round-trip neutral document source does not match the manifest"
        )
        assert {
            Entry.name: Entry.read_bytes() for Entry in TamperedPath.iterdir()
        } == Snapshot
    assert {
        Entry.name: Entry.read_bytes() for Entry in OutputPath.iterdir()
    } == Original
