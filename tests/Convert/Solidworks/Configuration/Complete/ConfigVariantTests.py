from typing import cast as CastValue

from tests.Convert.Solidworks.Configuration.Complete.RunPartConfig import RunPartConfig


# the complete archive preserves authored wire forms and inline ownership without native runtime access
def TestConfigForms() -> None:
    Result = RunPartConfig("authored", "ProveConfigVariants.py")
    assert Result["complete_replay"] is True
    assert Result["density_presence"] == [167, 99]
    assert Result["density_present_null"] is True
    assert Result["wire_lengths"] == {
        "nec8": -7,
        "nff4": -13,
        "n10c4": -19,
        "m": -29,
        "n1290": 2,
    }
    assert Result["direct_master"] == [22663, 22834, 94, 94]
    assert Result["map_base"] == 4 and Result["final_map_counter"] == 95
    assert Result["model_config_bytes"] == 22977
    assert (
        Result["model_config_sha256"]
        == "705ecba1d36e54c0bc5200a09e3f0624a3aa70ea138b8f34e8f14b4a5e575944"
    )
    Refusals = CastValue(dict[str, str], Result["refusals"])
    assert "wrong class" in Refusals["wrong_master"]
    assert "nonempty sheet metal master body list" in Refusals["populated_master"]
    assert "requires its modeled field" in Refusals["missing_density_field"]
