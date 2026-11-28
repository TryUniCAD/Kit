from argparse import ArgumentParser
from codecs import lookup
from hashlib import sha256
from importlib import import_module
from io import BytesIO
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from BuildOpenShellPlan import document, require
from CheckGeneratedShellOwners import verify_generated_shell_owners
from convert.adapters.solidworks.Archive.Bodies.BodyUnsupported import BodyUnsupported
from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.Preparation.Shells.BuildShellPart import BuildShellPart
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink

EPOCH = 1765500071
CASES = (
    ("OpenShellCalibration", 53, 41, 28, 2.8, (0, 0)),
    ("OpenShellTranslated", 62, 38, 36, 4.15, (8.5, -12.25)),
    ("OpenShellDistinct", 45, 68, 23, 1.875, (-3, 7.5)),
)


def digest(raw):
    return sha256(raw).hexdigest()


def verify_part(part, case):
    archive = SldprtArchive.from_bytes(part.BytesValue)
    require(archive.streams == part.StreamsValue and len(archive.streams) == 10,
            "the generated container differs from its ten computed stream owners")
    link = ReadNativeLink(archive, 0, ReadShells=True)
    headers = archive.require("Contents/Config-0-ModelHeader")
    header = ReadHeaderGraph(headers, 19000)
    config_data, config = WriteConfigMut(link.ConfigValue.RootValue, 19000, header)
    resolved_data, resolved = WriteResolMut(
        link.ResolvedValue.RootsValue,
        link.ResolvedValue.ExtraFields,
        19000,
        config.MapValue,
        link.ResolvedValue.ContextValue,
        WriteShell=True,
    )
    require(config_data == archive.require(link.ConfigName) and resolved_data == archive.require(link.StreamName),
            "the generated shell lost an exact typed config or resolved archive round trip")
    for combined in (
        lambda: ReadNativeLink(archive, 0, ReadChamfers=True, ReadShells=True),
        lambda: WriteResolMut(
            link.ResolvedValue.RootsValue, link.ResolvedValue.ExtraFields, 19000,
            config.MapValue, link.ResolvedValue.ContextValue,
            WriteShell=True, WriteChamfers=True,
        ),
    ):
        try:
            combined()
        except BodyUnsupported as error:
            require("combined shell and chamfer archives" in str(error), str(error))
        else:
            raise ValueError("unqualified combined shell and chamfer archive was admitted")
    owners = verify_generated_shell_owners(archive, link, case)
    return {"hash": digest(part.BytesValue), "bytes": len(part.BytesValue),
            "stream_hashes": {name: {"bytes": len(raw), "sha256": digest(raw)}
                              for name, raw in sorted(archive.streams.items())},
            "resolved_map_base": resolved.MapBase,
            "resolved_map_final": resolved.MapValue.CounterValue,
            "resolved_roots": len(resolved.RootsValue),
            "wall_m": owners["native_wall_m"], "linked_owner_proof": owners}


def main():
    parser = ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    for name in ("interchange.document.Behavior.DocumentIo",
                 "interchange.document.Validation.DocumentFeatureValidate",
                 "interchange.document.Validation.DocumentReferenceValidate",
                 "interchange.document.Validation.DocumentAssemblyValidate",
                 "interchange.document.Models.DocumentProvenance"):
        import_module(name)
    for encoding in ("utf-8", "utf-16-le", "cp1252", "latin-1"):
        lookup(encoding)
    pending = [(row, document(*row)) for row in CASES]
    active = True
    accesses = []

    def audit(event, arguments):
        if active and event in {"open", "subprocess.Popen", "os.system", "socket.connect", "socket.__new__", "ctypes.dlopen"}:
            accesses.append(event)
            raise PermissionError(f"shell compiler attempted an external access: {event}")

    sys.addaudithook(audit)
    products = {}
    for case, model in pending:
        name = case[0]
        locator = rf"C:\KitOpenShellGenerated01\Working\{name}.SLDPRT"
        options = WriteOptions(values={"final_destination": locator})
        artifact = BuildShellPart(model, BytesIO(), EPOCH, options)
        details = verify_part(artifact, case)
        details.update(locator=locator, neutral_sha256=model.source.sha256)
        products[name] = (artifact.BytesValue, details)
    require(len({details["hash"] for _, details in products.values()}) == len(pending),
            "model variations did not change complete native bytes")
    active = False
    args.output.mkdir()
    for name, (raw, details) in products.items():
        with (args.output / (name + ".SLDPRT")).open("xb") as file:
            file.write(raw)
    with (args.output / "Receipt.json").open("x", encoding="utf-8") as file:
        json.dump({"schema": "kit-sw2026-generated-open-shell-archives-v1",
                   "epoch": EPOCH, "runtime_external_accesses": accesses, "heldout_source_reads": 0,
                   "native_trial_run": False, "cases": {name: value for name, (_, value) in products.items()}},
                  file, indent=2, allow_nan=False)
        file.write("\n")


if __name__ == "__main__":
    main()
