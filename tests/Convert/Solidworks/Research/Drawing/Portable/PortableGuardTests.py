from tests.Convert.Solidworks.Research.Drawing.Portable.MakePortableCase import (
    MakeBlankCase,
)
from tests.Convert.Solidworks.Research.Drawing.Portable.MakePortableJob import (
    MakePortableJob,
)
from tests.Convert.Solidworks.Research.Drawing.Portable.MakePortableRejects import (
    BlankRejects,
)
from tests.Convert.Solidworks.Research.Drawing.Portable.RunPortableReject import (
    RunBlankReject,
)


# unsupported complete document requests must reject at the same guarded process boundary used by successful sdk construction
def TestBlankGuards() -> None:
    Request = MakeBlankCase("PortableReject", 13, 7)
    for JobValue in BlankRejects(MakePortableJob(Request)).values():
        RunBlankReject(JobValue)
