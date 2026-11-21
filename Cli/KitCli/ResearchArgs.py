from pathlib import Path as FilePath

from convert.Commands.CliOptions import CliOptions
from KitCli.DetectVerify import CanNativeVerify


# reader capability detection preserves legacy artifacts while requiring explicit verification status
def ResearchArgs(
    Options: CliOptions, RootPath: FilePath, ScriptPath: FilePath
) -> tuple[list[str], bool]:
    Arguments = list(Options.ToolArgs)
    LegacyReader = False
    if Options.Command == "run":
        Arguments = [*Arguments, "--batch-format", Options.ResearchTool]
    elif Options.ResearchTool in ("solidworks", "fusion", "corpus"):
        if any(
            Value.split("=", 1)[0] in ("--r", "--ro", "--roo", "--root")
            for Value in Arguments
        ):
            raise ValueError("Set research --root once, before the tool name")
        Arguments = ["--root", str(RootPath), *Arguments]
        if Options.ResearchTool in ("solidworks", "fusion"):
            if "--help" not in Arguments and "-h" not in Arguments:
                if CanNativeVerify(ScriptPath):
                    Arguments.append("--native-verify")
                else:
                    LegacyReader = True
    return Arguments, LegacyReader
