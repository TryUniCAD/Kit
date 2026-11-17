from types import MappingProxyType

from convert.adapters.solidworks.Archive.Bodies.NativeField import NativeField
from convert.adapters.solidworks.Archive.Bodies.Layouts.BodyLayouts import KBodyLayouts
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.AnnotationDetailFields import (
    KAnnotationDetailFields as KAnnotationDetailRules,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.AnnotationFrameFields import (
    KAnnotationFrameFields as KAnnotationFrameRules,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.AnnotationTablesFields import (
    KAnnotationTablesFields as KAnnotationTablesRules,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.AnnotationViewFields import (
    KAnnotationViewFields as KAnnotationViewRules,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.AssemblyFields import (
    KAssemblyFields as KAssemblyRules,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.BaseAnnotationFields import (
    KBaseAnnotationFields as KBaseAnnotationRules,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.CommonFields import (
    KCommonFields as KCommonRules,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.DimAnnotationFields import (
    KDimAnnotationFields as KDimAnnotationRules,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.ExternalFields import (
    KExternalFields as KExternalRules,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.FeatureFields import (
    KFeatureFields as KFeatureRules,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.FontFields import (
    KFontFields as KFontRules,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.FormatAnnotationFields import (
    KFormatAnnotationFields as KFormatAnnotationRules,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.GeometryFields import (
    KGeometryFields as KGeometryRules,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.HelperAnnotationFields import (
    KHelperAnnotationFields as KHelperAnnotationRules,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.LabelAnnotationFields import (
    KLabelAnnotationFields as KLabelAnnotationRules,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.MaterialFields import (
    KMaterialFields as KMaterialRules,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.ModelFields import (
    KModelFields as KModelRules,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.RecordFields import (
    KRecordFields as KRecordRules,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.UnitFields import (
    KUnitFields as KUnitRules,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.ViewFields import (
    KViewFields as KViewRules,
)

# current configuration owners reuse shared field rules while preserving their distinct reference profile
KConfigLayouts = MappingProxyType(
    {
        **KBodyLayouts,
        **KAnnotationDetailRules,
        **KAnnotationFrameRules,
        **KAnnotationTablesRules,
        **KAnnotationViewRules,
        **KAssemblyRules,
        **KBaseAnnotationRules,
        **KCommonRules,
        **KDimAnnotationRules,
        **KExternalRules,
        **KFeatureRules,
        **KFontRules,
        **KFormatAnnotationRules,
        **KGeometryRules,
        **KHelperAnnotationRules,
        **KLabelAnnotationRules,
        **KMaterialRules,
        **KModelRules,
        **KRecordRules,
        **KUnitRules,
        **KViewRules,
        "moExtFeature_c": (
            *KBodyLayouts["moExtFeature_c"][:-1],
            NativeField("Validate", "OrdinaryConfigExternal"),
        ),
    }
)
