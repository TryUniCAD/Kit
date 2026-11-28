import argparse
import json
from pathlib import Path
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[3])
    args = parser.parse_args()
    sys.path.insert(0, str(args.root.resolve() / "src"))
    from convert import open_document

    request = json.load(sys.stdin)
    options = {"include_brep": False, "include_tessellation": False, **request.get("options", {})}
    values = request.get("adapter_values")
    if values is None:
        document = open_document(Path(request["path"]), **options)
    else:
        from convert.adapters.base.ReadOptions import ReadOptions
        from convert.adapters.solidworks.Core.Adapter import SldprtAdapter

        document = SldprtAdapter().read(Path(request["path"]), ReadOptions(**options, values=values))
    print(document.to_json(indent=None))


if __name__ == "__main__":
    main()
