from argparse import ArgumentParser
from hashlib import sha256
from json import dumps, loads
from pathlib import Path
from struct import unpack_from

from VerifyRuntimeOwnerSources import Image


def read_name(image, rva):
    at = image.offset(rva)
    return image.data[at:image.data.index(b"\0", at)].decode("ascii")


def delay_import(image, address):
    directory, size = image.directories[13]
    first = image.offset(directory)
    for offset in range(first, first + size, 32):
        flags, name, handle, table, lookup, bound, unload, stamp = unpack_from("<8I", image.data, offset)
        if not any((flags, name, handle, table, lookup, bound, unload, stamp)):
            break
        if flags != 1:
            raise ValueError("expected RVA-based delay imports")
        entry = address - image.base - table
        if entry < 0 or entry % 8:
            continue
        at = image.offset(lookup)
        for step in range(0, entry + 8, 8):
            target, = unpack_from("<Q", image.data, at + step)
            if not target:
                break
        else:
            return {"module": read_name(image, name), "name": read_name(image, target + 2)}
    raise ValueError("delay import cell is absent")


def main():
    parser = ArgumentParser()
    parser.add_argument("--bin-directory", required=True, type=Path)
    parser.add_argument("--kernel", required=True, type=Path)
    parser.add_argument("--record", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    record = loads(args.record.read_bytes())
    if record.get("schema") != "kit.sw2026.downstream-face-registration-sources.v1":
        raise ValueError("face registration source schema differs")
    images = {}
    for module in record["modules"]:
        name = module["name"]
        image = Image(args.kernel if name == "PSKERNEL.dll" else args.bin_directory / name, module["sha256"])
        if len(image.data) != module["bytes"] or image.base != int(module["base"], 16):
            raise ValueError("original module bounds differ: " + name)
        images[name] = image
    for function in record["functions"]:
        images[function["module"]].verify_function(function)
    for row in record["instruction_windows"]:
        images[row["module"]].verify_span(row)
    for row in record["imports"]:
        image = images[row["source_module"]]
        identity = delay_import(image, int(row["iat"], 16)) if row["delay"] else image.imports()[row["iat"]]
        if identity != {"module": row["module"], "name": row["name"]}:
            raise ValueError("original import differs: " + row["name"])
    result = {
        "passed": True, "source_only": True, "native_runs": 0,
        "record_sha256": sha256(args.record.read_bytes()).hexdigest(),
        "tool_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "modules": len(images), "complete_functions": len(record["functions"]),
        "instruction_windows": len(record["instruction_windows"]), "verified_imports": len(record["imports"]),
    }
    with args.output.open("x") as writer:
        writer.write(dumps(result, indent=2, sort_keys=True) + "\n")
    print(dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
