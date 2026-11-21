from tests.Convert.Solidworks.Research.Drawing.SdkLinked.MakeLinkedJob import (
    MakeLinkedJob,
)
from tests.Convert.Solidworks.Research.Drawing.SdkLinked.MakeLinkRejects import (
    MakeLinkRejects,
)
from tests.Convert.Solidworks.Research.Drawing.SdkLinked.RunLinkedReject import (
    RunLinkedReject,
)


# unsupported drawing semantics must be refused by the same real child and complete file process used by passing cases
def TestLinkGuards() -> None:
    JobValue = MakeLinkedJob("LinkedReject", 37.9, 22.7, 14.3, "*Front", 1.0)
    for InputValue in MakeLinkRejects(JobValue).values():
        RunLinkedReject(InputValue)
