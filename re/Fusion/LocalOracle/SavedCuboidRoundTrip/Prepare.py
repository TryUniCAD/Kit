import argparse
from hashlib import sha256
import json
from math import isfinite
from pathlib import Path


def holdout_case(raw):
    try:
        name, width, depth, height, edit = raw.split(",")
        dims = [float(item) for item in (width, depth, height, edit)]
        if not name.isascii() or not name.isalnum() or any(not isfinite(item) or item <= 0 for item in dims):
            raise ValueError
        if dims[2] == dims[3]:
            raise ValueError
    except ValueError:
        raise argparse.ArgumentTypeError("holdout requires an alphanumeric name and four positive mm values: name,width,depth,height,edited height") from None
    return {"name": name, "dimensions_mm": dims[:3], "edited_height_mm": dims[3]}


def main():
    parser = argparse.ArgumentParser(description="Prepare one local Fusion cuboid corpus capture.")
    parser.add_argument("group", choices=("anchor", "auxiliary", "holdout"))
    parser.add_argument("output", type=Path)
    parser.add_argument("--holdout", type=holdout_case, action="append", default=[])
    args = parser.parse_args()
    if args.group == "holdout":
        if len(args.holdout) != 2 or len({item["name"].casefold() for item in args.holdout}) != 2:
            parser.error("holdout capture requires two distinctly named cases")
    elif args.holdout:
        parser.error("--holdout applies only to the holdout batch")
    script = Path(__file__).with_name("Capture.py").resolve()
    digest = sha256(script.read_bytes()).hexdigest()
    output = args.output.resolve()
    output.mkdir()
    config = output / "Request.json"
    config.write_text(json.dumps({
        "group": args.group,
        "holdout": args.holdout,
        "capture_script_sha256": digest,
    }, indent=2) + "\n", encoding="utf-8")
    entry = output / "Run.py"
    entry.write_text(
        "from hashlib import sha256\n"
        "from pathlib import Path\n"
        "import runpy\n"
        f"script = Path({str(script)!r})\n"
        f"if sha256(script.read_bytes()).hexdigest() != {digest!r}:\n"
        "    raise RuntimeError('Capture script changed after batch preparation')\n"
        f"runpy.run_path(str(script))['capture'](Path({str(config)!r}))\n",
        encoding="utf-8",
    )
    print(entry)


if __name__ == "__main__":
    main()
