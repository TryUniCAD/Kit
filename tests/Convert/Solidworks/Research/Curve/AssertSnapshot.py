from __future__ import annotations


# actual schema usage must be proven even when unused registry entries remain tentative
def AssertSnapshot(Snapshot: dict[str, object]) -> None:
    assert Snapshot["completed"] is True
    assert isinstance(Snapshot["used_schemas"], list)
    assert Snapshot["provisional_schemas"] == []
    assert Snapshot["missing_schemas"] == []
