from hashlib import sha256 as HashContent
from json import dumps as EncodeJson, loads as DecodeJson
from pathlib import Path as FilePath

from tests.CliResearch.EncoderRoundTrip.VerifySourcePin import KIdentityFields


# genuine legacy custody must remain distinct from newer writer artifacts and previously attached receipt sidecars
def MakeLegacy(Original: dict[str, bytes], LegacyPath: FilePath) -> dict[str, bytes]:
    Manifest = DecodeJson(Original["manifest.json"])
    assert Manifest["schema"] == 2
    Manifest["schema"] = 1
    _ = Manifest.pop("writer_input_sha256")
    for RoleName in ("reconstruction", "edited"):
        _ = Manifest[RoleName].pop("writer_input")
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
    LegacyPath.mkdir()
    for FileName, Content in Original.items():
        if FileName not in (
            "manifest.json",
            "reconstruction-writer-input.json",
            "edited-writer-input.json",
            "reconstruction-receipt.json",
            "edited-receipt.json",
        ):
            _ = (LegacyPath / FileName).write_bytes(Content)
    _ = (LegacyPath / "manifest.json").write_text(
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
    return {Entry.name: Entry.read_bytes() for Entry in LegacyPath.iterdir()}
