from convert.adapters.solidworks.Archive.Bodies.BodyContext import BodyContext
from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.solidworks.Archive.Bodies.Layouts.Config.Part.PartLayouts import (
    KPartLayouts,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.ContainerFields import (
    KContainerFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.FileRefFields import (
    KFileRefFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.SavedFolderFields import (
    KSavedFolderFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.SavedRefFields import (
    KSavedRefFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.SavedShapeFields import (
    KSavedShapeFields,
)
from convert.adapters.solidworks.Archive.Bodies.Layouts.Resolved.SavedSketchChainFields import (
    KSavedSketchChainFields,
)
from convert.adapters.solidworks.Archive.Resolved.Sweeps.SwapSwBodyMut import (
    SwapSwBodyMut,
)
from convert.adapters.solidworks.Archive.Resolved.Sweeps.SwSavedChoices import (
    KSwSavedChoices,
)


# saved result references are installed in the verified sweep context for this read only
def UseSwRefsMut(ContextValue: BodyContext) -> None:
    if (
        ContextValue.FlagsValue.get("cmgr_f658") != 1
        or ContextValue.UsageValue.SchemaCalls
    ):
        raise BodyUnsupported(
            "saved sweep references require the saved manager context"
        )
    LayoutValues = {
        **ContextValue.LayoutsValue,
        **KFileRefFields,
        "moPMarkRecord_c": KPartLayouts["moPMarkRecord_c"],
        "su_CDWordArray": KContainerFields["su_CDWordArray"],
        **KSavedFolderFields,
        **KSavedShapeFields,
        **KSavedSketchChainFields,
        **KSavedRefFields,
    }
    for NameValue, Choices in KSwSavedChoices.items():
        Pending = dict(Choices)
        LayoutValues[NameValue] = SwapSwBodyMut(LayoutValues[NameValue], Pending)
        if Pending:
            raise BodyUnsupported("saved sweep choices differ from the ordinary layout")
    ContextValue.LayoutsValue = LayoutValues
    ContextValue.SchemasValue = dict(ContextValue.SchemasValue) | dict.fromkeys(
        (
            "moBBoxCenterData_c",
            "moCStringHandle_c",
            "moEndFaceSurfIdRep_c",
            "moExtObject_c",
            "moFR_c",
            "moFaceRef_c",
            "moFromSktEntSurfIdRep_c",
            "moNotesAreaFtrFolder_c",
            "moPMarkRecord_c",
            "moPerBodyChooserData_c",
            "moSketchChain_c",
        ),
        (1,),
    )
