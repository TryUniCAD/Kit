from pathlib import Path as FilePath
from typing import cast as CastValue

from tests.Convert.Solidworks.ArchiveHeader.RunFreshHead import RunFreshHead

# the separately authored cases pin both role bytes and the standalone directory bytes
KFreshHeads = (
    (
        "straight",
        8,
        "50ef6738401680b928bee3e26b82279cc201b6e81574e79d1ae243874ab813e9",
        "79ef094e12b12747484d3b3000caee7ef859aac342ca31453875b9c4d218b7aa",
        "447c66014dff6dd9e3ac55aa02e6304b10fe4fc56da5697892475fdf81c2159f",
    ),
    (
        "unicode",
        24,
        "0d2c5b640d246628cea856c298ece2eb3970b7c0a166bda54ee6fc5e6cd59c9d",
        "4be113acd148afb4e2c411de484c6f2f0601cc61eb6fc57db099aea3ed6ec689",
        "787621047929ef65f66c2763678f6e0bf8d324e5d6ddf62612ac4b0759f1ee0b",
    ),
)


# generated role identity and the live configuration alias have distinct archive owners
def TestFreshHeads(TmpPath: FilePath) -> None:
    for CaseName, NextId, TopHash, ModelHash, ManagerHash in KFreshHeads:
        Report = RunFreshHead(CaseName, TmpPath)
        TopValue = CastValue(dict[str, object], Report["Header2"])
        ModelValue = CastValue(
            dict[str, object], Report["Contents/Config-0-ModelHeader"]
        )
        ManagerValue = CastValue(dict[str, object], Report["Contents/CMgrHdr2"])
        assert TopValue["sha256"] == TopHash
        assert ModelValue["sha256"] == ModelHash
        assert ManagerValue["sha256"] == ManagerHash
        assert TopValue["role"] == 0 and ModelValue["role"] == 1
        assert (
            TopValue["next_persistent_id"] == ModelValue["next_persistent_id"] == NextId
        )
        assert (
            TopValue["indices"]
            == ModelValue["indices"]
            == [2, 4, 5, 7, 9, 11, 13, 15, 16]
        )
        assert ManagerValue["entry_indices"] == [1, 2, 3, 4]
        assert ManagerValue["row_indices"] == [4] and ManagerValue["next_index"] == 5
        assert Report["direct_map"] == {"base": 4, "next": 4, "slots": [1, 2, 3]}


# omitted and conflicting owners must fail before any header graph can be published
def TestHeadRefusal(TmpPath: FilePath) -> None:
    assert RunFreshHead("refusals", TmpPath)["refused"] == [
        "foreign_part",
        "distinct_selector",
        "duplicate_count",
        "configuration_parent",
        "foreign_configuration_owner",
        "excluded_configuration",
        "comment_sidecar",
        "unallocated_part",
        "assembly_root",
        "early_save",
        "nonpart_extension",
    ]
