from convert.adapters.solidworks.Archive.Construction.Presentation.StyleInput import (
    StyleInput,
)


# the english iso profile uses native print widths in metres and authored labels for the otherwise empty style owners
def MakePartStyle() -> StyleInput:
    return StyleInput(
        1,
        "Century Gothic",
        "Continuous",
        1033,
        (0.00018, 0.00025, 0.00035, 0.0005, 0.0007, 0.001, 0.0014, 0.002),
        (),
        ("Description", "High Priority", "Low Priority", "Complete", "Reminder"),
        ("", "", ""),
    )
