from argparse import ArgumentParser
from pathlib import Path as FilePath


# file conversion exposes format configuration overwrite and native candidate publication controls
def AddConvertMut(Parser: ArgumentParser) -> None:
    _ = Parser.add_argument("Source", type=FilePath, metavar="SOURCE")
    _ = Parser.add_argument("Destination", type=FilePath, metavar="DESTINATION")
    _ = Parser.add_argument(
        "--from",
        dest="SourceFormat",
        metavar="FORMAT",
        help="Explicit reader format or alias",
    )
    _ = Parser.add_argument(
        "--to",
        dest="DestFormat",
        metavar="FORMAT",
        help="Explicit writer format or alias",
    )
    _ = Parser.add_argument(
        "--configuration",
        dest="Configuration",
        help="Named source and target configuration",
    )
    _ = Parser.add_argument(
        "--overwrite",
        dest="Overwrite",
        action="store_true",
        help="Replace existing output files",
    )
    _ = Parser.add_argument(
        "--allow-unverified-native",
        dest="AllowUnverifiedNative",
        action="store_true",
        help="Publish a SOLIDWORKS part candidate for vendor verification",
    )
    _ = Parser.add_argument(
        "--json",
        dest="JsonOutput",
        action="store_true",
        help="Print the conversion report as JSON",
    )
