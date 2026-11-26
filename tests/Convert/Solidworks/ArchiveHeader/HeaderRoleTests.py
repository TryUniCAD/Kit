from pathlib import Path as FilePath

from tests.Convert.Solidworks.ArchiveHeader.RunHeadReplay import RunHeadReplay


# distinct header data detects accidental reuse of the same stream for both roles
def TestHeadRoles(TmpPath: FilePath) -> None:
    HeaderHash, ModelHash = RunHeadReplay(
        TmpPath,
        "re/solidworks/v2026/corpus/local-import-readback/ConcaveOwned.SLDPRT",
        "fa1b84b7cd9e8860d549c599fdb536c6de965e3ec7b4ed5f53706cb57c743d33",
    )
    assert HeaderHash != ModelHash
    assert (
        HeaderHash == "0d8551d418c050d4f3d737edac10225af00146037f6eefa2b60511b8db4ad53d"
    )
    assert (
        ModelHash == "f4cce850be7777c5f6aad10d0bc46bda2e60448fac1ca4cde309df56063516aa"
    )
