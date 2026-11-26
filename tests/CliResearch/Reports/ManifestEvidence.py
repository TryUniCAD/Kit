from pathlib import Path as FilePath
from json import loads as LoadJson


# manifest identity must cover every selected control before a reader patch is accepted
def VerifyManifest(RunPath: FilePath) -> None:
    Manifest = LoadJson((RunPath / "Input-manifest-text.json").read_bytes())
    assert Manifest["status"] == "replayed_text_prefix"
    assert Manifest["shared_codecs"] == ["utf-16le", "utf-16le", "utf-16le", "ascii"]
    assert [Record["sha256"] for Record in Manifest["fusion_manifest_checks"]] == [
        Manifest["member_sha256"],
        *(Control["member_sha256"] for Control in Manifest["controls"]),
    ]
    assert all(
        Check["asset_id_matches"] and Check["snapshot_id_matches"]
        for Check in Manifest["fusion_manifest_checks"]
    )
    assert {Control["split"] for Control in Manifest["controls"]} == {
        "discovery",
        "qualification",
        "holdout",
    }
