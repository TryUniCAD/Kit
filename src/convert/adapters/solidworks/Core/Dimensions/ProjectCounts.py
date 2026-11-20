from collections import Counter
from dataclasses import replace as Replace


# unresolved count declarations must not become measured lengths or sketch distance constraints
def ProjectCounts(Dimensions, Counts, SketchCounts, OwnerId, ResolvedStream):
    if (
        Counts
        or SketchCounts
        or any(Dimension.kind == "instance_count" for Dimension in Dimensions)
    ):
        OccurrenceNames = Counter(Dimension.name for Dimension in Dimensions)
        Updated = []
        for Dimension in Dimensions:
            Count = Counts.get((OwnerId, Dimension.name))
            if (
                Count
                and Dimension.source_text.strip() == str(Count[0])
                and OccurrenceNames[Dimension.name] == 1
            ):
                Dimension = Replace(
                    Dimension,
                    kind=(
                        "instance_count"
                        if Dimension.kind == "instance_count"
                        else "sketch_pattern_count"
                    ),
                    value_mm=None,
                    native_value=Count[0],
                    native_offset=Count[1],
                    native_stream=ResolvedStream,
                    native_role="driving",
                    operands=(),
                    inch_display_value=None,
                )
            elif Dimension.kind == "instance_count" or (
                (OwnerId, Dimension.name) in SketchCounts
                and OccurrenceNames[Dimension.name] == 1
            ):
                Dimension = Replace(
                    Dimension,
                    kind=(
                        "instance_count"
                        if Dimension.kind == "instance_count"
                        else "sketch_pattern_count"
                    ),
                    value_mm=None,
                    native_value=None,
                    native_role=None,
                    native_offset=None,
                    native_stream=None,
                    operands=(),
                    inch_display_value=None,
                )
            Updated.append(Dimension)
        Dimensions = tuple(Updated)
    return Dimensions
