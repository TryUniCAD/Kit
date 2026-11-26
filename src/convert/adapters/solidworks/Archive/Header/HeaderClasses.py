from types import MappingProxyType

from convert.adapters.solidworks.Archive.Header.ReadHeaderBody import ReadHeadMut
from convert.adapters.solidworks.Archive.Header.ReadHeaderList import (
    ReadListMut,
    ReadLogMut,
    ReadStampMut,
    ReadTextListMut,
)
from convert.adapters.solidworks.Archive.Header.ReadSharedFile import (
    ReadFileRefMut,
    ReadNameMut,
)

# header class schemas are independent of the definition model archive
KHeaderClasses = MappingProxyType(
    {
        ("moHeader_c", 1): ReadHeadMut,
        ("moExtObject_c", 1): ReadFileRefMut,
        ("moExtObjectList_c", 1): ReadListMut,
        ("moCStringHandle_c", 1): ReadNameMut,
        ("moLogs_c", 1): ReadLogMut,
        ("moStamp_c", 1): ReadStampMut,
        ("suObList", 1): ReadListMut,
        ("su_CStringArray", 0): ReadTextListMut,
    }
)
