from hashlib import sha256 as HashContent
from json import dumps as EncodeJson, loads as DecodeJson
from pathlib import Path as FilePath

from tests.CliResearch.EncoderRoundTrip.VerifySourcePin import KIdentityFields


# self consistent custody changes must not hide writer inputs that produce different native candidate bytes
def RebindWriter(OutputPath: FilePath, Payload: bytes) -> None:
    ManifestPath = OutputPath / "manifest.json"
    Manifest = DecodeJson(ManifestPath.read_bytes())
    assert Manifest["schema"] == 2
    Artifact = Manifest["edited"]["writer_input"]
    assert Artifact["path"] == "edited-writer-input.json"
    _ = (OutputPath / Artifact["path"]).write_bytes(Payload)
    WriterHash = HashContent(Payload).hexdigest()
    Artifact.update({"sha256": WriterHash, "bytes": len(Payload)})
    Manifest["writer_input_sha256"]["edited"] = WriterHash
    Identity = {FieldName: Manifest[FieldName] for FieldName in KIdentityFields}
    Identity["writer_input_sha256"] = Manifest["writer_input_sha256"]
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
    _ = ManifestPath.write_text(
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
