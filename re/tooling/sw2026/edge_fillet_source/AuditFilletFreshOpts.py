from argparse import ArgumentParser
from hashlib import sha256
from json import dumps
from pathlib import Path
from subprocess import run
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "materials"))

from MaterialPe import PeImage


MODULES = {
    "sldmopartu.dll": "aa3fa88eeb5349c8ac2161ce9b3f18ab4e23417598c6b57719c88d5d6c178da9",
    "sldgcu.dll": "77b7376933f483eb5c1e3a93e22241f07a001a824023f5498d880d9b45fae594",
    "sldgciParau.dll": "96f244063a5e8badc547fca3655506ae8eb99197653168efa232d775b55b96ce",
    "swccu.dll": "d5a8a3f3c9e4f108650242dab99ae8f9c9b8edb0e3fd2e04c185964f79d1ba7c",
}

FRAMES = (
    ("sldmopartu.dll", "fillet constructor", 0x180269D00, {
        0x180269E70: "[rsi + 0xc20]",
        0x180269E77: "0x1803ec788",
    }),
    ("swccu.dll", "word array constructor", 0x31A3BCA0, {
        0x31A3BCBD: "xor\teax, eax",
        0x31A3BCC7: "dword ptr [rbx + 0x10], eax",
    }),
    ("sldmopartu.dll", "fillet solve", 0x1802A6CC0, {
        0x1802A87CA: "[r12 + 0xc20]",
        0x1802A87D2: "[rsp + 0xf8], r8",
        0x1802A88DD: "0x1803e8de0",
    }),
    ("sldgcu.dll", "public kernel bridge", 0x43CA0B70, {
        0x43CA0B96: "[rsp + 0x228]",
        0x43CA0B9E: "[r11 - 0x30], rax",
        0x43CA0CF1: "0x43e7f9a0",
    }),
    ("sldgcu.dll", "kernel bridge dispatch", 0x43E7F9A0, {
        0x43E7FB88: "[rsp + 0xf8], rax",
        0x43E7FD12: "0x43f5c8b0",
    }),
    ("sldgciParau.dll", "fillet entry and other option branch", 0x33061FE0, {
        0x33062174: "[rsp + 0x6e8]",
        0x3306217C: "[rsp + 0x1d0], rax",
        0x3306233D: "0x3306cbb0",
        0x33062FBB: "dword ptr [rbx + 0x10], 0x0",
        0x33062FC1: "r14d, 0x1",
        0x3306373B: "0x330780d0",
    }),
    ("sldgciParau.dll", "ordinary fillet dispatch", 0x3306CBB0, {
        0x3306CCC2: "[rbp + 0x228]",
        0x3306CCD4: "[rbp + 0x18], rcx",
        0x3306D4BB: "[rbp + 0x20]",
        0x3306D4BF: "[rsp + 0xf0], rax",
        0x3306D5D1: "0x33070920",
    }),
    ("sldgciParau.dll", "ordinary fillet first solve", 0x33070920, {
        0x33070A74: "[rsp + 0x650]",
        0x33071B93: "dword ptr [rdi + 0x10], 0x0",
        0x33071B99: "r12d, 0x1",
        0x33071BA7: "0x33071c49",
        0x33071BF2: "byte ptr [rdx]",
        0x33071D42: "[rsp + 0x10c]",
        0x3307207A: "0x47d7",
        0x33072087: "r12d, r12d",
        0x330720A4: "0x330780d0",
    }),
    ("sldgciParau.dll", "solved option save", 0x330780D0, {
        0x33078109: "esi, 0x6",
        0x3307811C: "0x330b64b8",
        0x33078126: "0x33078110",
        0x3307813D: "dword ptr [rcx], eax",
        0x330781B3: "dword ptr [rcx + 0x14], eax",
    }),
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def observe(image, name, address, fragments):
    start, end = image.range(address)
    require(start == address, f"{name} does not begin at its recorded entry")
    instructions = run(
        ("/usr/bin/objdump", "--disassemble", "--x86-asm-syntax=intel",
         f"--start-address={start:#x}", f"--stop-address={end:#x}", str(image.path)),
        capture_output=True, text=True, check=True,
    ).stdout.lower().splitlines()
    for location, fragment in fragments.items():
        require(any(row.startswith(f"{location:x}:") and fragment in row for row in instructions),
                f"{name} has a different instruction at {location:#x}")
    return image.pin(name, start, end) | {"instruction_sites": [hex(value) for value in fragments]}


def main():
    parser = ArgumentParser()
    parser.add_argument("--modules", type=Path, required=True)
    parser.add_argument("--array", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    images = {name: PeImage(args.array if name == "swccu.dll" else args.modules / name) for name in MODULES}
    require({name: image.sha256 for name, image in images.items()} == MODULES, "exact PE module identities differ")
    imports = (
        ("sldmopartu.dll", 0x1803EC788, "??0su_CDWordArray@@"),
        ("sldmopartu.dll", 0x1803E8DE0, "?ramFilletEdge@@"),
        ("sldgcu.dll", 0x43F5C8B0, "?gci_ramFilletEdge@GCP@@"),
        ("sldgciParau.dll", 0x330B64B8, "?SetAtGrow@su_CDWordArray@@"),
    )
    bound = []
    for module, slot, prefix in imports:
        entry = images[module].imports()[slot]
        require(entry["name"].startswith(prefix), f"unexpected import at {slot:#x}")
        bound.append({"module": module, "slot": hex(slot), "target": entry})
    receipt = {
        "schema": "kit.sw2026.ordinary-fillet-fresh-options.v1",
        "oracle_build": "34.5.2.0604",
        "module_sha256": MODULES,
        "rechecked_functions": [
            {"module": module, **observe(images[module], name, address, fragments)}
            for module, name, address, fragments in FRAMES
        ],
        "bound_imports": bound,
        "fresh_count": 0,
        "save_helper_default_word_count": 6,
        "native_processes_started": 0,
        "fillet_writer_output_count": 0,
    }
    data = (dumps(receipt, indent=2, sort_keys=True) + "\n").encode()
    with args.report.open("xb") as output:
        output.write(data)
    print(sha256(data).hexdigest())


if __name__ == "__main__":
    main()
