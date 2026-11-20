from argparse import ArgumentParser
from json import dumps, loads
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from convert.adapters.solidworks.Archive.Construction.Metadata.KeywordConfig import KeywordConfig
from convert.adapters.solidworks.Archive.Construction.Metadata.KeywordDim import KeywordDim
from convert.adapters.solidworks.Archive.Construction.Metadata.KeywordFeature import KeywordFeature
from convert.adapters.solidworks.Archive.Construction.Metadata.MakeKeywords import MakeKeywords
from convert.adapters.solidworks.Core.Native import ParseXml


RUNTIME_EVENTS = frozenset({
    "open", "os.listdir", "os.scandir", "subprocess.Popen", "os.system",
    "os.exec", "os.posix_spawn", "os.fork", "os.forkpty", "ctypes.dlopen",
})


def make_feature(row):
    dimensions = tuple(
        KeywordDim(dimension["name"], dimension["value"], dimension.get("unit"))
        for dimension in row.get("dimensions", ())
    )
    return KeywordFeature(
        row["id"], row["name"], row["kind"], row["tag"], dimensions,
        tuple(row.get("children", ())), row.get("dissectable"), row.get("root"),
    )


def encode_model(source):
    configurations = tuple(
        KeywordConfig(row["id"], row["name"], row["material"])
        for row in source["configurations"]
    )
    features = tuple(make_feature(row) for row in source["features"])
    return MakeKeywords(source["name"], source["timestamp"], configurations, features)


def describe_model(payload):
    root = ParseXml(payload)
    return {
        "root": [root.tag, root.get("id"), root.get("Name")],
        "order": [[row.tag, row.get("id"), row.get("Name")] for row in root],
        "types": [row.get("Type") for row in root],
        "children": [[row.get("id"), row.get("DissectableChildren")] for row in root
                     if "DissectableChildren" in row.attrib],
        "dissectable": [[row.get("id"), row.get("Dissectable")] for row in root
                        if "Dissectable" in row.attrib],
        "dimensions": [[row.get("id"), [[child.get("Name"), child.text] for child in row]]
                       for row in root if len(row)],
    }


def run_guarded(mode, payload):
    denied = []
    active = True

    def audit(event, _arguments):
        if active and event in RUNTIME_EVENTS:
            denied.append(event)
            raise PermissionError(f"keyword process attempted runtime access: {event}")

    sys.addaudithook(audit)
    try:
        if mode == "write":
            output = encode_model(loads(payload))
        else:
            output = dumps(describe_model(payload)).encode("utf-8")
    finally:
        active = False
    if denied:
        raise PermissionError(f"keyword process attempted runtime access: {denied[0]}")
    return output


def main():
    parser = ArgumentParser(description="Check typed SOLIDWORKS KeyWords emission")
    parser.add_argument("mode", choices=("read", "write"))
    options = parser.parse_args()
    payload = sys.stdin.buffer.read()
    sys.stdout.buffer.write(run_guarded(options.mode, payload))


if __name__ == "__main__":
    main()
