from pathlib import Path as FilePath
from tempfile import TemporaryDirectory as TempDirectory

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
from tests.Convert.Solidworks.Research.AdapterBridge.PrepareProbe import PrepareProbe


# both authored circle profiles must reach the measurement gate and keep their independent radial intent on readback
def TestCircleWrite() -> None:
    RegistryValue = GetRegistry()
    WriterValue = RegistryValue.GetWriter("SOLIDWORKS.SLDPRT")
    assert WriterValue.info.part_extensions == (".sldprt",)
    with TempDirectory() as RootValue:
        for IsTop in (False, True):
            NameValue = (
                "sdk public top radius" if IsTop else "sdk public front diameter"
            )
            DocumentValue = MakeWriteCircle(NameValue, IsTop)
            TargetPath = FilePath(RootValue) / NameValue / (NameValue + ".SLDPRT")
            assert WriterValue.supports(DocumentValue, TargetPath)
            RawValue = PrepareProbe(DocumentValue, TargetPath, 1795000061)
            CheckCircRead(TargetPath, DocumentValue)
            CheckCircRead(RawValue, DocumentValue)
            CheckCircPolicy(DocumentValue, TargetPath)
