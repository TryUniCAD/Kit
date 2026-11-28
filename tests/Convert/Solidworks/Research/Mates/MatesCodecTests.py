from pathlib import Path as FilePath

from tests.Convert.Solidworks.Research.Assembly.PlanarMateInput import MakeMateInput
from tests.Convert.Solidworks.Research.Assembly.RunMateBundle import RunMateBundle
from tests.Convert.Solidworks.Research.Mates.AssertMatesProbe import AssertMates
from tests.Convert.Solidworks.Research.Mates.RunMatesProbe import RunMatesProbe


# a guarded neutral bundle must preserve typed planar endpoints across native file and process boundaries
def TestMatesCodec(TmpPath: FilePath) -> None:
    ParentPath, _ = RunMateBundle(MakeMateInput("typedmates"), TmpPath / "pair")
    AssertMates(RunMatesProbe(ParentPath))
