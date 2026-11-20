from json import loads as LoadJson


# count hypotheses and scalar roles must agree with the same held out native stream
def VerifyOwnership(RunPath):
    Scalars = LoadJson((RunPath / "Input-scalar-streams.json").read_bytes())
    Ownership = Scalars["members"]["Contents/Config-0-ResolvedFeatures"]["ownership"]
    Patterns = [
        Record
        for Record in Ownership["records"]
        if Record["ownership_status"] == "pattern_count_hypothesis"
    ]
    assert {Record["count_hypothesis"]["feature_id"] for Record in Patterns} == {
        65,
        257,
    }
    for Record in Patterns:
        Pattern = Record["count_hypothesis"]
        assert Pattern["count"] == 11
        assert {
            CopyValue["offset"] - Record["offset"]
            for CopyValue in Pattern["matching_copies"]
            if CopyValue["format"] == "<d"
        } == {373, 397}
    assert Ownership["role_counts"]["display"].get("no_matching_declaration", 0) == 57
    Selected = [
        Record
        for Record in Ownership["records"]
        if Record["selected_among_display_copies"]
    ]
    assert Selected
    assert all(Record["native_trailer"]["role"] == "driving" for Record in Selected)
