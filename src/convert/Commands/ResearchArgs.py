from argparse import ArgumentParser, REMAINDER as KArgRemainder
from pathlib import Path as FilePath

from convert.Commands.ResearchTools import KResearchScripts


# deterministic research tools need a trusted checkout and unchanged downstream arguments
def AddResearchMut(
    Parser: ArgumentParser, Tools: tuple[str, ...] | None = None
) -> None:
    _ = Parser.add_argument(
        "--root",
        dest="ResearchRoot",
        type=FilePath,
        required=True,
        help="Trusted checkout whose research code and SDK will execute",
    )
    if Tools is None:
        _ = Parser.add_argument(
            "--offline",
            dest="Offline",
            action="store_true",
            help="Decode without native API verification; acceptance remains pending",
        )
    _ = Parser.add_argument(
        "ResearchTool",
        choices=tuple(KResearchScripts) if Tools is None else Tools,
        help="Research tool or campaign format",
    )
    _ = Parser.add_argument(
        "ToolArgs",
        nargs=KArgRemainder,
        metavar="ARG",
        help="Arguments forwarded unchanged to the selected research tool; use TOOL --help",
    )
