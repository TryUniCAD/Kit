from typing import cast as CastValue

from tests.Convert.Solidworks.Configuration.FieldModes.RunModeCase import RunModeCase

# the same native views start at different offsets and counters across independent parts
KRepeatSpans = (
    ("ladder", [22240, 4, 84], [24252, 4, 95]),
    ("concave", [20463, 4, 79], [22475, 4, 90]),
)

# the ten authored native view identities establish repeat ordering independently of its count
KViewNames = [
    "*Normal To",
    "*Front",
    "*Back",
    "*Left",
    "*Right",
    "*Top",
    "*Bottom",
    "*Isometric",
    "*Trimetric",
    "*Dimetric",
]


# the real view rows and physical predicate words need coverage separate from authored scalars
def TestModeWitness() -> None:
    for CaseName, StartFrame, EndFrame in KRepeatSpans:
        ReportValue = RunModeCase(CaseName, WitnessOnly=True)
        Branches = CastValue(list[dict[str, object]], ReportValue["branch_witnesses"])
        assert [
            (
                RowValue["mode"],
                RowValue["compared"],
                RowValue["predicate"],
                RowValue["width"],
            )
            for RowValue in Branches
        ] == [
            ("Equals", 2, True, 10),
            ("Greater", 0, False, 0),
            ("NotCondition", None, True, 4),
        ]
        assert [RowValue["raw_words"] for RowValue in Branches] == [
            [0, -1431655766, -1145324613],
            [],
            [0],
        ]
        Repeat = CastValue(dict[str, object], ReportValue["native_repeat"])
        assert (Repeat["start"], Repeat["end"], Repeat["width"]) == (
            StartFrame,
            EndFrame,
            2012,
        )
        assert Repeat["anchor_slots"] == [1, 2, 3]
        assert Repeat["class_slot"] == StartFrame[2]
        Views = CastValue(list[dict[str, object]], Repeat["views"])
        assert [RowValue["name"] for RowValue in Views] == KViewNames
        assert [(RowValue["class"], RowValue["schema"]) for RowValue in Views] == [
            ("moView_c", 1)
        ] * 10
        assert [RowValue["index"] for RowValue in Views] == list(
            range(StartFrame[2] + 1, EndFrame[2])
        )
        Intervals = [CastValue(list[int], RowValue["interval"]) for RowValue in Views]
        assert [EndOffset - StartOffset for StartOffset, EndOffset in Intervals] == [
            160,
            140,
            210,
            210,
            212,
            208,
            214,
            220,
            220,
            218,
        ]
