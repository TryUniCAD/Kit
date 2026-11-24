from argparse import ArgumentParser
from json import dumps as DumpJson
from pathlib import Path as FilePath


# process compatibility needs an independent receiver for the forwarded catalogue arguments
def ReceiveArgs() -> None:
    Parser = ArgumentParser()
    for Option in (
        "--catalogue",
        "--directory",
        "--workers",
        "--input",
        "--batch-format",
    ):
        _ = Parser.add_argument(Option)
    _ = Parser.add_argument("--author-samples", action="store_true")
    _ = Parser.add_argument("--pause", action="store_true")
    _ = Parser.add_argument("--resume", action="store_true")
    Options = Parser.parse_args()
    if Options.directory is not None:
        FilePath(Options.directory).mkdir(parents=True, exist_ok=False)
    print(DumpJson(vars(Options)))
    raise SystemExit(7)


if __name__ == "__main__":
    ReceiveArgs()
