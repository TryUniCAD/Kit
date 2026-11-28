from json import dumps as DumpJson, loads as LoadJson
from pathlib import Path as FilePath
from runpy import run_path as RunPath
from sys import argv as ArgValues, stderr as ErrorOutput
from typing import Callable, cast as CastValue


# the callable must consume persisted semantic input in a separate ordinary process
def LegacyChild() -> int:
    RootPath = FilePath(__file__).resolve().parents[5]
    Script = RootPath / "re/Fusion/LegacyBodyAppearance/LegacyValues.py"
    Symbols = RunPath(str(Script))
    BuildLegacy = CastValue(
        Callable[[object], tuple[bytes, bytes]], Symbols["build_legacy_values"]
    )
    try:
        Request = LoadJson(FilePath(ArgValues[1]).read_text(encoding="utf-8"))
        Definition, Properties = BuildLegacy(Request)
    except ValueError as Failure:
        print(str(Failure), file=ErrorOutput)
        return 1
    Output = FilePath(ArgValues[2])
    _ = (Output / "Definition.bin").write_bytes(Definition)
    _ = (Output / "Properties.bin").write_bytes(Properties)
    print(
        DumpJson(
            {"definition_bytes": len(Definition), "property_bytes": len(Properties)}
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(LegacyChild())
