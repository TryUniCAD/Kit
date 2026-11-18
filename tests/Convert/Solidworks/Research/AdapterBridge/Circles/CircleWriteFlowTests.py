from io import BytesIO
from pathlib import Path as FilePath
from tempfile import TemporaryDirectory as TempDirectory
from unittest.mock import patch as PatchValue

from convert import write_document as WriteDoc
from convert.adapters.base.TransferContract import TransferMode
from convert.api.ApiContext import GetRegistry
from tests.Convert.Solidworks.Research.AdapterBridge.Circles.CheckCircPolicy import (
    CheckCircPolicy,
)
from tests.Convert.Solidworks.Research.AdapterBridge.Circles.CheckCircRead import (
    CheckCircRead,
)
from tests.Convert.Solidworks.Research.AdapterBridge.Circles.MakeWriteCircle import (
    MakeWriteCircle,
)


# the registered circle writer must exercise real staging native capability accounting and normal readback for both qualified profiles
def TestCircleWrite() -> None:
    RegistryValue = GetRegistry()
    WriterValue = RegistryValue.GetWriter("SOLIDWORKS.SLDPRT")
    assert WriterValue.info.Extensions == (".sldprt",)
    assert not WriterValue.info.AliasNames
    assert len(WriterValue.info.NativeCaps) == 6
    with TempDirectory() as RootValue:
        for IsTop in (False, True):
            NameValue = (
                "sdk public top radius" if IsTop else "sdk public front diameter"
            )
            DocumentValue = MakeWriteCircle(NameValue, IsTop)
            TargetPath = FilePath(RootValue) / NameValue / (NameValue + ".SLDPRT")
            assert WriterValue.supports(DocumentValue, TargetPath)
            with PatchValue(
                "convert.adapters.solidworks.Core.Writing.EmitNativeMut.ReadTime",
                return_value=1795000061,
            ) as ClockValue:
                ResultValue = WriteDoc(
                    DocumentValue,
                    TargetPath,
                    allow_carrier=False,
                    values={"require_native_transfers": True},
                )
                StreamValue = BytesIO()
                StreamResult = WriteDoc(
                    DocumentValue,
                    StreamValue,
                    destination_format="solidworks.sldprt",
                    allow_carrier=False,
                    values={
                        "require_native_transfers": True,
                        "final_destination": str(TargetPath),
                    },
                )
                assert ClockValue.call_count == 2
            assert TargetPath.read_bytes() == StreamValue.getvalue()
            assert (
                ResultValue.path == TargetPath.resolve() and StreamResult.path is None
            )
            assert ResultValue.bytes_written == StreamResult.bytes_written
            assert ResultValue.application_usable and ResultValue.vendor_loadable
            assert StreamResult.application_usable and StreamResult.vendor_loadable
            assert not ResultValue.dropped and not StreamResult.dropped
            assert len(ResultValue.native_capabilities) == 6
            assert all(
                Value.mode is TransferMode.KNative for Value in ResultValue.transfers
            )
            CheckCircRead(TargetPath, DocumentValue)
            CheckCircRead(StreamValue.getvalue(), DocumentValue)
            CheckCircPolicy(DocumentValue, TargetPath)
