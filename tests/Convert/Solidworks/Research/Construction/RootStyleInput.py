# independently authored style settings supply model dependencies without vendor preference or fixture data
def RootStyleInput(NameValue: str) -> dict[str, object]:
    return {
        "standard": 1,
        "font_name": NameValue + " font",
        "line_style_name": NameValue + " continuous",
        "language_id": 1033,
        "print_widths_m": [0.0001 * (IndexValue + 1) for IndexValue in range(8)],
        "exclusion_names": [],
        "task_labels": [
            NameValue + " " + TextValue
            for TextValue in ("description", "high", "low", "complete", "reminder")
        ],
        "cutlist_expressions": ["item", "description", "stock"],
    }
