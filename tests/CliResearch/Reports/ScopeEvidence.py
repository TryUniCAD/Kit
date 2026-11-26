from hashlib import file_digest as FileDigest
from pathlib import Path as FilePath


# partial routing and provenance must refer to the exact renamed archived input
def VerifyScopePins(InputPath: FilePath, Audit: dict[str, object]) -> None:
    with InputPath.open("rb") as Stream:
        assert Audit["source_sha256"] == FileDigest(Stream, "sha256").hexdigest()
    assert (Audit["feature_layer"], Audit["provenance_layer"]) == ("partial", "partial")
