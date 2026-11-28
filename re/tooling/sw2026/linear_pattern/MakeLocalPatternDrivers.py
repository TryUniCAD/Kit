from dataclasses import dataclass

from convert.adapters.solidworks.Archive.Construction.Patterns.Drivers.PatAnnoValues import PatAnnoValues
from convert.adapters.solidworks.Archive.Construction.Patterns.Drivers.PatDriveStyle import (
    CheckPatStyles,
    KPatDriveSlots as DRIVER_SLOTS,
    PatDriveStyle,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Drivers.PutPatDriveMut import PutPatDriveMut


@dataclass(frozen=True, slots=True)
class PatternDriverStyle:
    name: str
    annotation_view: str | None
    label_m: tuple[float, float, float]
    design_intent: bool
    selected_leader: int


def typed_style(style):
    return PatDriveStyle(style.name, style.annotation_view, style.label_m, style.design_intent, style.selected_leader)


def typed_styles(styles):
    if type(styles) is not tuple or not all(type(style) is PatternDriverStyle for style in styles):
        raise ValueError("pattern requires six explicitly styled driving or dormant display owners")
    return tuple(typed_style(style) for style in styles)


def check_styles(styles):
    CheckPatStyles(typed_styles(styles))


def driver_views(root, style):
    return PatAnnoValues(root, typed_style(style))


def make_drivers(owner, root, styles, count, pitch, witnesses, allocator):
    return PutPatDriveMut(owner, root, typed_styles(styles), count, pitch, witnesses, allocator)
