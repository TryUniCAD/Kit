from __future__ import annotations

# base model construction requires generated presentation and unit graphs rather than saved document defaults
KBaseStyles = """
BaseStyleData = NewDetails(
    standard=1,
    font_name=NamePrefix + "font",
    line_style_name=NamePrefix + "line",
    language_id=1033,
    print_widths_m=tuple(0.0001 * (WidthIndex + 1) for WidthIndex in range(8)),
    exclusion_names=(),
    task_labels=tuple(NamePrefix + "task" + str(TaskIndex) for TaskIndex in range(5)),
    cutlist_expressions=("part-id", "assembly-id", "weldment-id"),
)
BaseUserUnits = NewUnits(
    length_unit="mm", angle_unit="degree", unit_system="mmgs", decimal_places=4
)
BaseAnalysisUnits = NewUnits(
    length_unit="m", angle_unit="radian", unit_system="mks", decimal_places=6
)
"""
