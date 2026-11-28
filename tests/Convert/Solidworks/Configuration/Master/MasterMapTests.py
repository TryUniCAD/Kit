from typing import cast as CastValue

from tests.Convert.Solidworks.Configuration.Master.RunMasterCase import RunMasterCase


# a complete authored inherited map must keep every class and object identity
def TestMasterMap() -> None:
    Result = RunMasterCase("full_map")
    assert Result["map"] == {
        "base": 4,
        "entries": 118,
        "slot_span": [1, 118],
        "classes": 30,
        "objects": 88,
        "after_each_operation": "same_entries_and_inverse_lookups",
    }
    Proof = CastValue(dict[str, object], Result["proof"])
    assert Proof["extent"] == [0, 155]
    assert Proof["counter"] == [119, 119]
    assert (Proof["slot"], Proof["body_count"]) == (None, 0)
    assert (
        Proof["wire_sha256"]
        == Proof["emitted_sha256"]
        == ("2a1536c54d55a425602ec103b9f887b109f8091fde58c1b4b0d45265a461992b")
    )
