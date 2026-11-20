from json import loads as LoadJson


# reserved control results must remain proposals without leaking input identities into advisor requests
def VerifyHoldout(Output, TmpPath, Source, Evidence):
    Stall = LoadJson((Output / "FileStall.json").read_bytes())
    assert Stall["source_sha256"] == Evidence["input_sha256"]
    assert Stall["focus"] == "ambiguous_dimension"
    assert Stall["signed_extrusion_layout_refuted_on_searched_fields"]
    Request = LoadJson((Output / "FileAdvice/Request.json").read_bytes())
    assert "no match" in Request["packet"]["discovery_summary"]
    assert Source.name not in str(Request["packet"])
    assert Evidence["input_sha256"] not in str(Request["packet"])
    Answer = LoadJson((Output / "FileAdvice/Advice.json").read_bytes())
    assert Answer["status"] == "proposal" and Answer["verified_rule"] is False
    assert (TmpPath / "Calls").read_text().splitlines() == ["called"]
    Experiments = LoadJson((Output / "FileExperiments.json").read_bytes())
    assert Experiments["advisor_selection"] == "vary blind cut depth"
    CutResult, BossResult = Experiments["results"]
    assert CutResult["controlled_change"] == Experiments["advisor_selection"]
    assert CutResult["status"] == BossResult["status"] == "no_target_match"
    assert (
        CutResult["comparisons"][0]["input_value"],
        CutResult["comparisons"][0]["control_value"],
    ) == (0.004, 0.005)
    assert (
        BossResult["comparisons"][0]["input_value"],
        BossResult["comparisons"][0]["control_value"],
    ) == (0.01, 0.012)
