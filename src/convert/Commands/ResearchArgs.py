from argparse import ArgumentParser, REMAINDER as KArgRemainder
from pathlib import Path as FilePath

from convert.Commands.ResearchTools import KResearchScripts


# deterministic research tools need a trusted checkout and unchanged downstream arguments
def AddResearchMut(
    Parser: ArgumentParser, Tools: tuple[str, ...] = tuple(KResearchScripts)
) -> None:
    _ = Parser.add_argument(
        "--root",
        dest="ResearchRoot",
        type=FilePath,
        required=True,
        help="Trusted checkout whose research code and SDK will execute",
    )
    _ = Parser.add_argument(
        "ResearchTool",
        choices=Tools,
        help="Research tool or campaign format",
    )
    _ = Parser.add_argument(
        "ToolArgs",
        nargs=KArgRemainder,
        metavar="ARG",
        help="Arguments forwarded unchanged to the selected research tool; use TOOL --help",
    )
