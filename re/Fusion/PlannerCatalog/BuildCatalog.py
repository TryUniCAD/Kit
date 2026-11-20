from argparse import ArgumentParser
from json import dumps
from pathlib import Path
from shutil import rmtree
from tempfile import mkdtemp

from ApiInventory import CollectApi
from CatalogDatabase import WriteBundle
from CatalogRows import CatalogRows
from EvidenceInventory import CollectCommands, CollectNative, CollectRecipes


# publication refuses existing destinations so collection cannot overwrite a prior planner inventory
def BuildCatalog(ApiRoot, ResearchRoot, OutputPath, CommandsPath=None, AllCsv=False):
    ApiRoot = ApiRoot.resolve(strict=True)
    ResearchRoot = ResearchRoot.resolve(strict=True)
    OutputPath = OutputPath.absolute()
    if OutputPath.exists() or OutputPath.is_symlink():
        raise ValueError("Output already exists; choose a fresh catalogue directory")
    if not ApiRoot.is_dir() or not ResearchRoot.is_dir():
        raise ValueError("API and research roots must be directories")
    Rows = CatalogRows()
    Version = CollectApi(Rows, ApiRoot)
    CollectNative(Rows, ResearchRoot)
    CollectRecipes(Rows, ResearchRoot)
    if CommandsPath is not None:
        CommandsPath = CommandsPath.resolve(strict=True)
        CollectCommands(
            Rows,
            CommandsPath,
            "commands:current",
            ResearchRoot if CommandsPath.is_relative_to(ResearchRoot) else None,
        )
        CapturedVersion = Rows.Sources["commands:current"][4]
        if CapturedVersion != Version:
            Rows.AddGap(
                "ui_application_version_mismatch",
                "commands:current",
                Details={"captured_version": CapturedVersion, "api_version": Version},
            )
    else:
        Rows.AddGap("ui_current_capture_missing", "api:manifest")
    for SourcePath in sorted(Path(__file__).parent.glob("*.py")):
        Rows.AddSource(
            "collector:" + SourcePath.name, "collector", SourcePath.name, SourcePath
        )
    OutputPath.parent.mkdir(parents=True, exist_ok=True)
    TemporaryPath = Path(mkdtemp(prefix=".CatalogBuild", dir=OutputPath.parent))
    try:
        Summary = WriteBundle(Rows, TemporaryPath, Version, AllCsv)
        if OutputPath.exists():
            raise ValueError("Output appeared during collection; refusing publication")
        TemporaryPath.rename(OutputPath)
        return Summary
    finally:
        if TemporaryPath.exists():
            rmtree(TemporaryPath)


# explicit inputs make catalogue provenance independent of the callers current working directory
def MainRun():
    Parser = ArgumentParser(
        description="Collect Fusion metadata into indexed SQLite and CSV without importing the vendor API"
    )
    Parser.add_argument(
        "--api-root",
        required=True,
        type=Path,
        help="Installed Contents/Api/Python/packages/adsk/defs/adsk directory",
    )
    Parser.add_argument(
        "--research-root", type=Path, default=Path(__file__).resolve().parents[3]
    )
    Parser.add_argument(
        "--commands",
        type=Path,
        help="Read-only command capture JSON from the intended session",
    )
    Parser.add_argument("--output", required=True, type=Path)
    Parser.add_argument(
        "--all-csv", action="store_true", help="Also export every raw relational table"
    )
    Arguments = Parser.parse_args()
    try:
        Summary = BuildCatalog(
            Arguments.api_root,
            Arguments.research_root,
            Arguments.output,
            Arguments.commands,
            Arguments.all_csv,
        )
    except (ValueError, OSError, KeyError, TypeError, SyntaxError) as Error:
        Parser.exit(2, "Catalogue collection failed: " + str(Error) + "\n")
    print(dumps(Summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    MainRun()
