from argparse import ArgumentParser
from hashlib import sha256
from json import dump
from pathlib import Path

from convert.adapters.solidworks.Archive.Bodies.BodyWriter import BodyWriter
from convert.adapters.solidworks.Archive.Bodies.WriteBodyMut import WriteBodyMut
from convert.adapters.solidworks.Archive.Bodies.Writing.WriteNodeMut import WriteNodeMut
from convert.adapters.solidworks.Archive.Cmgr.MakeCmgrContext import MakeCmgrContext
from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Archive.Counts.EncodeCount import EncodeCount
from convert.adapters.solidworks.Archive.Maps.ArchiveMaps import ArchiveMaps
from convert.adapters.solidworks.Archive.Resolved.MakeResolvedCtx import MakeResolvedCtx
from convert.adapters.solidworks.Archive.Resolved.UseShellCtxMut import UseShellCtxMut
from convert.adapters.solidworks.Archive.Resolved.WriteMbsMut import WriteMbsMut
from convert.adapters.solidworks.Archive.Scalars.EncodeScalar import EncodeScalar
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink

CASES = {
    "OpenShell.SLDPRT": ("73a4330ef831d38273ef6128bcbff15e4a105421219293ae5454941a3c7301cd", 11424, 14106, 0.0028),
    "OpenShellEdited.SLDPRT": ("c0be437a8c13a50c940b0d9cee51d369865abf3fa0a7ed62610fb9c76eb4b810", 11532, 14214, 0.00353),
}
VERSION = 19000


def require(condition, message):
    if not condition:
        raise ValueError(message)


def replay_manager(root):
    writer = BodyWriter(ArchiveMaps(1), MakeCmgrContext(VERSION, None, ReadLinked=True), WriteBodyMut)
    WriteNodeMut(writer, root)
    return bytes(writer.OutputValue)


def replay_resolved(config_map, model_root, resolved):
    context = MakeResolvedCtx(VERSION, config_map, resolved.ContextValue, None, ChamferLayout=True)
    UseShellCtxMut(context)
    writer = BodyWriter(ArchiveMaps(resolved.MapBase, config_map), context, WriteBodyMut)
    writer.OutputValue.extend(EncodeScalar(resolved.MapBase, "u32"))
    writer.OutputValue.extend(EncodeCount(len(resolved.RootsValue)))
    for row in resolved.RootsValue:
        WriteNodeMut(writer, row)
    WriteMbsMut(writer, model_root, resolved.ExtraFields)
    return bytes(writer.OutputValue)


def replay_case(disclosure, name):
    identity, start, end, thickness = CASES[name]
    raw = (disclosure / name).read_bytes()
    require(sha256(raw).hexdigest() == identity, "disclosed native source hash changed")
    archive = SldprtArchive.from_bytes(raw, name)
    linked = ReadNativeLink(archive, 0, ReadShells=True)
    manager, configuration, resolved = linked.ManagerValue, linked.ConfigValue, linked.ResolvedValue
    root = manager.RootValue
    stock, shell = resolved.RootsValue[-2:]
    require((configuration.MapValue.CounterValue, manager.MapValue.CounterValue,
             resolved.MapBase, resolved.MapValue.CounterValue, len(resolved.RootsValue))
            == (109, 19, 109, 313, 20), "linked archive maps changed")
    require((shell.ClassValue.NameValue, shell.IndexValue, shell.StartOffset, shell.EndOffset)
            == ("moShell_c", 273, start, end), "resolved shell ownership changed")
    atom = shell.FieldsValue["f538"]
    atom_link, = root.FieldsValue["f360"].FieldsValue["f450"]
    require(atom_link["key"] == atom.FieldsValue["f140"] == atom_link["o"].FieldsValue["f08"]
            and atom_link["o"].FieldsValue["f90"]["items"] == [{"v": stock.FieldsValue["f08"]}]
            and atom_link["o"].FieldsValue["fd0"]["items"] == [{"v": shell.FieldsValue["f08"]}],
            "manager atom link changed")
    value = shell.FieldsValue["f818"].FieldsValue["f850"][0]["o"].FieldsValue["ff0"]
    metres = value.FieldsValue["f28"].FieldsValue["f58"]
    require(value.ClassValue.NameValue == "ThreeDRadiusDim_c"
            and metres == thickness, "actual thickness changed")
    manager_data = replay_manager(root)
    config_data, config_replay = WriteConfigMut(configuration.RootValue, VERSION, configuration.HeaderValue)
    resolved_data = replay_resolved(config_replay.MapValue, configuration.RootValue, resolved)
    result = {}
    for stream, encoded in (("Contents/CMgr", manager_data), (linked.ConfigName, config_data),
                            (linked.StreamName, resolved_data)):
        require(encoded == archive.require(stream), f"{stream} typed replay differs")
        result[stream] = {"sha256": sha256(encoded).hexdigest(), "bytes": len(encoded)}
    return {"sha256": identity, "config_base": resolved.MapBase, "resolved_end": resolved.MapValue.CounterValue,
            "shell_span": [start, end], "thickness_metres": metres, "streams": result}


def main():
    parser = ArgumentParser()
    parser.add_argument("--disclosure", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    cases = {name: replay_case(args.disclosure, name) for name in CASES}
    with args.output.open("x", encoding="utf-8") as stream:
        dump({"schema": "kit-open-shell-typed-archive-replay-v1", "cases": cases,
              "read_replay_identical": 6, "writer_publications": 0, "heldout_sources_read": 0},
             stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")


if __name__ == "__main__":
    main()
