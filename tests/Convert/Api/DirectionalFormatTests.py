from contextlib import redirect_stdout as RedirectOutput
from dataclasses import replace as ReplaceValue
from io import BytesIO as BytesIo
from io import StringIO as StringIo
from json import loads as LoadJson
from typing import cast as CastValue

import pytest as Pytest
from typing_extensions import override as Override

from convert.Commands.CliOptions import CliOptions
from convert.Commands.RunCommand import RunCommand
from convert.adapters import AdapterInfo, AdapterNotFoundError, AdapterRegistry
from convert.adapters.json.Adapter import JsonAdapter
import convert.api.ApiContext as ApiContext
from tests.Convert.Api.Fusion.AdapterCases import AdapterCase


# reuse the interoperable json reader with an alias reserved for reading
class SnapshotReader(JsonAdapter):

    # alias metadata lets the real codec exercise separate reader and writer lookup
    @property
    @Override
    def info(self) -> AdapterInfo:
        return ReplaceValue(
            super().info,
            aliases=("interchange.snapshot",),
            extensions=(".json", ".snapshot"),
        )


# both registration orders preserve the read alias without granting publication through it
@Pytest.mark.parametrize("ReaderFirst", (False, True))
def TestAliasReplay(ReaderFirst: bool) -> None:
    RegistryValue = AdapterRegistry()
    ReaderValue = SnapshotReader()
    WriterValue = JsonAdapter()
    if ReaderFirst:
        RegistryValue.register_reader(ReaderValue)
        RegistryValue.register_writer(WriterValue)
    else:
        RegistryValue.register_writer(WriterValue)
        RegistryValue.register_reader(ReaderValue)

    DocumentValue = AdapterCase("rectangle")
    StreamValue = BytesIo()
    ResultValue = RegistryValue.write(
        DocumentValue, StreamValue, format_id="interchange.json"
    )
    assert ResultValue.bytes_written == len(StreamValue.getvalue())
    assert (
        RegistryValue.read(StreamValue.getvalue(), format_id="INTERCHANGE.SNAPSHOT")
        == DocumentValue
    )
    BlockedValue = BytesIo()
    with Pytest.raises(AdapterNotFoundError, match="no writer registered"):
        _ = RegistryValue.write(
            DocumentValue, BlockedValue, format_id="interchange.snapshot"
        )
    assert BlockedValue.getvalue() == b""

    RegistryValue.register_writer(JsonAdapter(), replace=True)
    assert RegistryValue.reader("interchange.snapshot") is ReaderValue
    RegistryValue.register_reader(JsonAdapter(), replace=True)
    with Pytest.raises(AdapterNotFoundError, match="no reader registered"):
        _ = RegistryValue.reader("interchange.snapshot")


# the format command reports read and write names independently in both output modes
def TestAliasCli(MonkeyPatch: Pytest.MonkeyPatch) -> None:
    RegistryValue = AdapterRegistry()
    RegistryValue.register_reader(SnapshotReader())
    RegistryValue.register_writer(JsonAdapter())
    MonkeyPatch.setattr(ApiContext, "KAdapterRegistry", RegistryValue)
    Options = CliOptions()
    Options.Command = "formats"
    Options.JsonOutput = True
    JsonOutput = StringIo()
    with RedirectOutput(JsonOutput):
        RunCommand(Options)
    (Format,) = CastValue(list[dict[str, object]], LoadJson(JsonOutput.getvalue()))
    assert Format["extensions"] == [".json", ".snapshot"]
    assert Format["aliases"] == ["interchange.snapshot"]
    assert Format["write_extensions"] == [".json"]
    assert Format["write_aliases"] == []
    Options.JsonOutput = False
    TableOutput = StringIo()
    with RedirectOutput(TableOutput):
        RunCommand(Options)
    Header, ValueRow = TableOutput.getvalue().splitlines()
    Columns = dict(zip(Header.split("\t"), ValueRow.split("\t"), strict=True))
    assert LoadJson(Columns["extensions"]) == [".json", ".snapshot"]
    assert LoadJson(Columns["write_extensions"]) == [".json"]
