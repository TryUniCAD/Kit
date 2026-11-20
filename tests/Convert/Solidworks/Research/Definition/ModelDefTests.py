from tests.Convert.Solidworks.Research.Definition.CheckFreshModelDef import (
    CheckFreshDef,
)
from tests.Convert.Solidworks.Research.Definition.CheckModelDefRejection import (
    CheckDefReject,
)


# native definition preparation must independently consume every fresh variant and reject invalid profiles
def TestModelDef() -> None:
    Reports = CheckFreshDef()
    CheckDefReject(Reports[0])
