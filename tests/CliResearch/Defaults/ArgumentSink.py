from argparse import ArgumentParser
from hashlib import sha256 as HashBytes
from json import dumps as DumpJson, loads as LoadJson
from pathlib import Path as FilePath


# process compatibility needs an independent receiver for the forwarded catalogue arguments
def ReceiveArgs() -> None:
    Parser = ArgumentParser()
    Catalogue = Parser.add_mutually_exclusive_group()
    for Option in ("--catalogue", "--solidworks-catalogue", "--fusion-catalogue"):
        _ = Catalogue.add_argument(Option, dest="catalogue")
    for Option in (
        "--directory",
        "--workers",
        "--input",
        "--batch-format",
        "--auth",
        "--advisor",
        "--authoring-grid",
        "--solidworks-sha256",
        "--fusion-sha256",
    ):
        _ = Parser.add_argument(Option)
    _ = Parser.add_argument("--author-samples", action="store_true")
    _ = Parser.add_argument("--pause", action="store_true")
    _ = Parser.add_argument("--resume", action="store_true")
    Options = Parser.parse_args()
    if Options.advisor is not None and Options.author_samples:
        Parser.error(
            "authoring rejects decoder advice with grid "
            + str(Options.authoring_grid)
            + " and authentication "
            + str(Options.auth)
        )
    Result = vars(Options)
    if Options.catalogue is not None:
        RawBytes = FilePath(Options.catalogue).read_bytes()
        Expected = getattr(Options, Options.batch_format + "_sha256")
        if Expected is not None and HashBytes(RawBytes).hexdigest() != Expected:
            Parser.error("catalogue SHA-256 does not match")
        Result["catalogue_content"] = LoadJson(RawBytes)
    if Options.directory is not None:
        FilePath(Options.directory).mkdir(parents=True, exist_ok=False)
    print(DumpJson(Result))
    raise SystemExit(7)


if __name__ == "__main__":
    ReceiveArgs()
