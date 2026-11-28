from tests.Convert.Solidworks.Research.Drawing.Model.RunModelCase import RunModelCase
from tests.Convert.Solidworks.Research.Drawing.Portable.AssertPortable import (
    AssertPortable,
)
from tests.Convert.Solidworks.Research.Drawing.Portable.MakePortableCase import (
    MakeBlankCase,
)
from tests.Convert.Solidworks.Research.Drawing.Portable.MakePortableJob import (
    MakePortableJob,
)
from tests.Convert.Solidworks.Research.Drawing.Portable.RunPortableCase import (
    RunPortableCase,
)


# two deterministic sdk constructions per fresh design must match a separate independent research construction at the complete file boundary
def TestBlankRoots() -> None:
    HashesValue: set[object] = set()
    for Label, Numerator, Denominator in (
        ("PortableAlpha", 13, 7),
        ("PortableBeta", 17, 11),
        ("PortableGamma", 3, 19),
        ("PortableDelta", 23, 9),
    ):
        Request = MakeBlankCase(Label, Numerator, Denominator)
        JobValue = MakePortableJob(Request)
        Result = RunPortableCase(JobValue)
        assert Result == RunPortableCase(JobValue)
        AssertPortable(Result)
        Independent = RunModelCase(
            {"schema": "kit.sw2026.sdk-drawing-model-process.v1", "request": Request}
        )
        assert Result["artifact_base64"] == Independent["artifact_base64"]
        assert Result["artifact_sha256"] == Independent["artifact_sha256"]
        HashesValue.add(Result["artifact_sha256"])
    assert len(HashesValue) == 4
