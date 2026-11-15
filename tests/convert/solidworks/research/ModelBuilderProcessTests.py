from __future__ import annotations

from json import loads as LoadJson
from pathlib import Path as FilePath

from tests.convert.solidworks.research.ModelBuilderProcess import RunBuilders


def TestFreshGraphs(TmpPath: FilePath) -> None:
    Small = RunBuilders(TmpPath, 1, 1234.5, "first-")
    Large = RunBuilders(TmpPath, 7, 7654.25, "independent-構成-")
    assert Small.returncode == 0, Small.stdout + Small.stderr
    assert Large.returncode == 0, Large.stdout + Large.stderr
    First = LoadJson(Small.stdout)
    Second = LoadJson(Large.stdout)
    assert First["configuration_names"] == ["first-0"]
    assert Second["configuration_names"] == [
        f"independent-構成-{Index}" for Index in range(7)
    ]
    assert First["configuration_ids"] == [0]
    assert Second["configuration_ids"] == list(range(7))
    assert First["next_configuration_id"] == 1
    assert Second["next_configuration_id"] == 7
    assert First["density_kg_m3"] == 1234.5
    assert Second["density_kg_m3"] == 7654.25
    assert First["journal_name"] == "first- journal"
    assert Second["journal_name"] == "independent-構成- journal"
    assert First["runtime_reads"] == []
    assert Second["runtime_reads"] == []
    assert (
        Second["stream_bytes"]["Contents/CMgr"] > First["stream_bytes"]["Contents/CMgr"]
    )
    assert (
        Second["stream_bytes"]["Contents/Definition"]
        > First["stream_bytes"]["Contents/Definition"]
    )
    assert not First["vendor_loadable"] and not Second["vendor_loadable"]
    assert not First["application_usable"] and not Second["application_usable"]
