from convert.formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel


# the live topology needs one resolution rule so a journal history yields the entities fusion reports
def ResolveLive(Journal: JournalModel) -> frozenset[int]:
    Live: set[int] = set()
    for State in Journal.States:
        for Board in State.Boards:
            for Change in Board.Changes:
                if Change.OldRef != -1:
                    Live.discard(Change.OldRef)
                if Change.NewRef != -1:
                    Live.add(Change.NewRef)
    return frozenset(Live)
