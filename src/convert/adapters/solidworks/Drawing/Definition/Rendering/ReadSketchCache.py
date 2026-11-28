from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Drawing.Definition.Rendering.NeedViewMap import (
    NeedViewMap,
)


# a present cache can have no saved records without losing its pointer state
def ReadSketchCache(FieldsValue: Mapping[str, object]) -> tuple[bool, int | None]:
    Presence = FieldsValue.get("has_fb50")
    if type(Presence) is not int or Presence not in (0, 1):
        raise BodyUnsupported("drawing view state requires canonical cache presence")
    if Presence == 0:
        if FieldsValue.get("fb50") is not None:
            raise BodyUnsupported(
                "drawing view state has conflicting absent cache data"
            )
        return False, None
    CacheFields = NeedViewMap(FieldsValue.get("fb50"))
    CountValue = CacheFields.get("n")
    if set(CacheFields) != {"n"} or type(CountValue) is not int or CountValue != 0:
        raise BodyUnsupported(
            "drawing view state supports only wire empty sketch caches"
        )
    return True, CountValue
