from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.Lines.IsLineState import IsLineState
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord


# profile geometry must remain wholly local with no partial contour selection spatial ownership or additional modeled profile state
def CheckPrismProf(ProfileValue: ArchiveNode) -> None:
    Fields = ProfileValue.FieldsValue
    for FieldName in ("f390", "f3dc", "pd_has_fe8", "pd_f118", "f42c", "f3c0"):
        if Fields.get(FieldName) != 0:
            raise ValueError("cache free prism has unsupported profile modes")
    if Fields.get("pd_f100") != 4 or Fields.get("pd_f11c") != (
        -7 if ProfileValue.ClassValue.NameValue == "moOriginProfileFeature_c" else -1
    ):
        raise ValueError("cache free prism has an alternate local profile branch")
    if any(
        Fields.get(FieldName) is not None
        for FieldName in ("orig_dim_feature", "f3b8", "pd_f110", "f388")
    ):
        raise ValueError("cache free prism has profile dependencies or shared geometry")
    for FieldName in ("d5c0", "f3e8", "pd_f128", "pd_f148"):
        if not IsLineState(Fields.get(FieldName)):
            raise ValueError(
                "cache free prism has contour caches or extra profile references"
            )
    Contours = NativeRecord(Fields.get("ca30"))
    if (
        Contours.get("f10") != 3
        or not IsLineState(Contours.get("f238"))
        or Contours.get("n238") != 0
        or not IsLineState(Contours.get("f168"))
    ):
        raise ValueError("cache free prism has unqualified contour selections")
