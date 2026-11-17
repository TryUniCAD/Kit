from tests.Convert.Solidworks.Research.Definition.CheckFreshModelDef import (
    CheckFreshModelDef,
)
from tests.Convert.Solidworks.Research.Definition.CheckModelDefRejection import (
    CheckModelDefRejection,
)


# native definition preparation must independently consume every fresh variant and reject invalid profiles
def TestModelDefinition() -> None:
    Reports = CheckFreshModelDef()
    CheckModelDefRejection(Reports[0])
