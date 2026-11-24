from json import dumps as DumpJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess


# shortcut compatibility needs a separate git root with a real downstream argument receiver
def PresetFiles(Directory: FilePath) -> tuple[FilePath, FilePath]:
    Checkout = Directory / "trusted checkout"
    Checkout.mkdir()
    _ = RunProcess(("git", "init", str(Checkout)), capture_output=True, check=True)
    (Checkout / "src/convert").mkdir(parents=True)
    ScriptPath = Checkout / "re/automation/InferenceGrid/RunFeatureCatalogue.py"
    ScriptPath.parent.mkdir(parents=True)
    _ = ScriptPath.write_bytes(
        FilePath(__file__).with_name("ArgumentSink.py").read_bytes()
    )
    ConfigPath = Directory / "RunDefaults.json"
    Catalogue = Checkout / "catalogue with spaces.json"
    _ = Catalogue.write_text(DumpJson({"selected": "saved preset"}), encoding="utf-8")
    Preset = {
        "root": str(Checkout),
        "output_root": str(Directory / "run outputs"),
        "options": {
            "--catalogue": str(Catalogue),
            "--workers": "18",
            "--author-samples": True,
            "--authoring-grid": "three-values",
        },
    }
    _ = ConfigPath.write_text(
        DumpJson(
            {"schema_version": 1, "formats": {"solidworks": Preset, "fusion": Preset}}
        ),
        encoding="utf-8",
    )
    return ConfigPath, Checkout
