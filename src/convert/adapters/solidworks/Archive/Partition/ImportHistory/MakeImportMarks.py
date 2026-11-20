from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode

# a new kernel partition establishes its own initial mark before any retained application event
KFirstMarkId = 1

# a new application history allocates delta handles independently of kernel identities
KFirstDeltaKey = 1


# retained import marks need reversible chronological links and fresh independent allocations
def MakeImportMarks(RootIndex: int, EventCount: int) -> tuple[XmtNode, ...]:
    MarkCount = EventCount + 1
    IndexValues = tuple(range(RootIndex + MarkCount, RootIndex, -1))
    MarkIds = range(KFirstMarkId, KFirstMarkId + MarkCount)
    DeltaKeys = (0, *range(KFirstDeltaKey, KFirstDeltaKey + EventCount))
    return tuple(
        XmtNode(
            IndexValue,
            4,
            {
                "preceding": IndexValues[Position - 1] if Position else 0,
                "first_following": (
                    IndexValues[Position + 1] if Position + 1 < MarkCount else 0
                ),
                "next_sibling": 0,
                "prev_sibling": 0,
                "n_new_nodes": 0,
                "n_del_nodes": 0,
                "n_copy_mod_nodes": 0,
                "delta_key": DeltaKey,
                "delta_is_forward": 0,
                "id": MarkId,
            },
        )
        for Position, (IndexValue, MarkId, DeltaKey) in enumerate(
            zip(IndexValues, MarkIds, DeltaKeys, strict=True)
        )
    )
