from convert.adapters.solidworks.Archive.Construction.Patterns.Input.PatAnnoBases import (
    KPatAnnoLeft,
    KPatAnnoTop,
)
from convert.adapters.solidworks.Archive.Construction.System.PartSystem import (
    PartSystem,
)
from convert.adapters.solidworks.Archive.Construction.Views.Annotations.AnnoViewInput import (
    AnnoViewInput,
)
from convert.adapters.solidworks.Archive.Construction.Views.Annotations.MakeAnnoView import (
    KAnnoWorld,
)
from convert.adapters.solidworks.Archive.Construction.Views.Annotations.PutAnnoCatalog import (
    PutAnnoCatalog,
)


# the selected principal mode needs its observed ordered annotation catalogue and ordinary unassigned state
def PutPrincViewMut(SystemValue: PartSystem, Version: int, *, NeedsLeft: bool) -> None:
    TopView = AnnoViewInput("*Top", KPatAnnoTop)
    FrontView = AnnoViewInput("*Front", KAnnoWorld)
    Views = (
        (TopView, AnnoViewInput("*Left", KPatAnnoLeft), FrontView)
        if NeedsLeft
        else (TopView, FrontView)
    )
    _ = PutAnnoCatalog(SystemValue.RootValue, Version, Views, None, (None,))
