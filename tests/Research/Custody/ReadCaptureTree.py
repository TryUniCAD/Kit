from hashlib import sha256 as GetDigest
from json import dumps as EncodeJson


# reports need an independent identity derived from actual git tree bytes
def ReadCaptureTree(TreeRows: bytes) -> tuple[dict[str, dict[str, str]], str]:
    CurrentTree: dict[str, dict[str, str]] = {}
    for RowValue in TreeRows.split(b"\0"):
        if not RowValue:
            continue
        Metadata, PathBytes = RowValue.split(b"\t", 1)
        ModeValue, KindValue, BlobId = Metadata.decode("ascii").split()
        assert KindValue == "blob"
        CurrentTree[PathBytes.decode("utf-8")] = {"mode": ModeValue, "git_blob": BlobId}
    return (
        CurrentTree,
        GetDigest(
            EncodeJson(
                CurrentTree, sort_keys=True, separators=(",", ":"), ensure_ascii=True
            ).encode("ascii")
        ).hexdigest(),
    )
