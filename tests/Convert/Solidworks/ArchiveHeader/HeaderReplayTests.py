from pathlib import Path as FilePath

from tests.Convert.Solidworks.ArchiveHeader.RunHeadReplay import RunHeadReplay


# separate stream roots must replay completely from the same immutable native control
def TestHeadReplay(TmpPath: FilePath) -> None:
    HeaderHash, ModelHash = RunHeadReplay(
        TmpPath,
        "re/solidworks/v2026/corpus/ladder/L1_boss.SLDPRT",
        "55e5a9840cc78a1d4b3ac4b8de3f37540695494e4d7a0edfb3cd3a2a876e2ac6",
    )
    assert (
        HeaderHash
        == ModelHash
        == ("9e3d68bd031e4797a2f05504cf8962e5e3a337d2816ec963194165371d5b4659")
    )
