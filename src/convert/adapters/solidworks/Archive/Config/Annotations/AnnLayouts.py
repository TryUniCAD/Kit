from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.AnnotationFrameFields import (
    KAnnotationFrameFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.BaseAnnotationFields import (
    KBaseAnnotationFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.FormatAnnotationFields import (
    KFormatAnnotationFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.MaterialFields import (
    KMaterialFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.ToleranceHelperFields import (
    KTolHelperFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.ContainerFields import (
    KContainerFields,
)

# the detailing section owns an inline annotation defaults body
KAnnDefs = "moAnnotationDefs_c"

# tolerance preferences own framed rows independently from dimension definitions
KTolHelper = "moGTolDataHelper_c"

# scoped detailing fields share only the format and array records they actually own
KAnnLayouts = MappingProxyType(
    {
        **KBaseAnnotationFields,
        **KAnnotationFrameFields,
        **KTolHelperFields,
        "utCharFormat_c": KFormatAnnotationFields["utCharFormat_c"],
        "utLineWidth_c.Serialize0": KMaterialFields["utLineWidth_c.Serialize0"],
        "su_CStringArray": KContainerFields["su_CStringArray"],
    }
)
