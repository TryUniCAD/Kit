from dataclasses import replace as ReplaceValue
from io import BytesIO as BytesIo

import pytest as Pytest

from convert.adapters import AdapterInfo, AdapterNotFoundError, AdapterRegistry
from convert.adapters.json.Adapter import JsonAdapter
from tests.Convert.Api.Fusion.AdapterCases import AdapterCase


# reuse the interoperable JSON reader with a read-specific catalog alias
class SnapshotReader(JsonAdapter):

    # alias metadata lets the real codec exercise separate reader and writer lookup
    @property
    def info(self) -> AdapterInfo:
        return ReplaceValue(super().info, aliases=("interchange.snapshot",))


# both registration orders preserve the read alias without granting publication through it
@Pytest.mark.parametrize("ReaderFirst", (False, True))
def TestDirectionalFormatRoundTrip(ReaderFirst: bool) -> None:
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
