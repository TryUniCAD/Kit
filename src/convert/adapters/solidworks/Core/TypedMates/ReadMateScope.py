from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# complete graph admission must describe perpendicular orientation separately while preserving existing aligned scope metadata exactly
def ReadMateScope(NodesValue: tuple[ArchiveNode, ...], ItemCount: int) -> str:
    Perpendicular = tuple(
        NodeValue
        for NodeValue in NodesValue
        if NodeValue.ClassValue.NameValue == "moMatePerpendicular"
    )
    if Perpendicular:
        if len(NodesValue) != 1 or ItemCount != 2:
            raise ValueError(
                "perpendicular graph requires one mate and two occurrences"
            )
        return "ordinary_perpendicular_single_mate_two_direct_part_occurrences"
    if len(NodesValue) == 1 and ItemCount == 2:
        return "ordinary_aligned_single_mate_two_direct_part_occurrences"
    return "ordinary_aligned_mates_direct_part_occurrences"
