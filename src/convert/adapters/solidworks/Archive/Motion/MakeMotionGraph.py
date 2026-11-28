from convert.adapters.solidworks.Archive.Motion.MotionLayouts import (
    KMotionKey,
    KMotionMgr,
)
from convert.adapters.solidworks.Archive.Motion.MotionStudy import MotionStudy
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Strings.CStringValue import CStringValue


# the inactive ordinary manager must build a fresh scene without authored tracks tasks or native settings
def MakeMotionGraph(InputValue: MotionStudy) -> ArchiveNode:
    if type(InputValue) is not MotionStudy:
        raise TypeError("motion requires an explicit typed study identity")
    StudyValue = ArchiveNode(KMotionKey, MotionKeyValues(InputValue))
    StudyValue.FieldsValue["f2c8"] = {"f08": StudyValue, "taskCount": 0, "f38": 0}
    return ArchiveNode(
        KMotionMgr, {"f30": -1, "studies": ({"o": StudyValue},), "f50": 0}
    )


# stable constructor values are distinct from the independent study identity and its declared caption
def MotionKeyValues(InputValue: MotionStudy) -> dict[str, object]:
    FieldsValue: dict[str, object] = dict.fromkeys(
        (
            "f118",
            "componentCount",
            "attributeCount",
            "f0d8",
            "f0dc",
            "f1f8",
            "f208",
            "f238",
            "f250",
            "f268",
            "f2a0",
            "f308",
            "f32c",
            "f2c2",
            "f4e0",
            "f1c8",
        ),
        0,
    )
    FieldsValue.update(
        f0f8=CStringValue(InputValue.NameValue, True),
        f108=CStringValue("{" + str(InputValue.IdentityValue).upper() + "}", True),
        f110=CStringValue("", True),
        f128=0.0,
        f1b4=-1,
        f1c0=4 | (1 << 1),
        f1d0=None,
        f0b0={"selected": 0, "count": 0},
        f0e0=0.0,
        f0e8=-1.0,
        f148=-1.0,
        hasHolder=1,
    )
    return FieldsValue
