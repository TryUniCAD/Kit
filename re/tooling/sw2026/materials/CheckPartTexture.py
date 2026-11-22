from codecs import lookup
from hashlib import sha256
import json
from pathlib import Path
from struct import calcsize, pack
from subprocess import run
import sys


HERE = Path(__file__).resolve()
sys.path[:0] = [str(HERE.parents[4] / "src"), str(HERE.parents[1]), str(HERE.parent)]

from MakeHeadAliasCase import frame_lanes, header
from ProvePartMaterialVisual import require, worker
from convert.adapters.solidworks.Archive.Config.Material.ReadPartVisual import ReadPartVisual


def text(value=""):
    payload = value.encode("ascii")
    return pack("<B", len(payload)) + payload


def tag(name):
    payload = name.encode("ascii")
    return pack("<3H", 0xFFFF, 1, len(payload)) + payload


def primary_texture():
    vector = tuple(index / 8 * (-1 if index % 2 == 0 else 1) for index in range(1, 14))
    name = "Kit texture Ω".encode("utf-16-le")
    return (pack("<13d", *vector) + pack("<BHB", 0xFF, 0xFFFE, len(name) // 2)
            + name + pack("<hiddi", -314, -271828, 2.75, -4.125, 913))


def renderer():
    return (
        bytes(8) + text() + bytes(calcsize("<BI10fi5fi2f"))
        + text() + bytes(calcsize("<I2f")) + text()
        + bytes(calcsize("<3fifi13f")) + text() + pack("<f", 0.5)
    )


def pbr():
    return (
        bytes(48 * 4) + text() * 5 + pack("<f", 0.25) + text() * 2
        + bytes(calcsize("<i6f")) + text() * 2 + bytes(calcsize("<2f"))
        + text() * 2 + text("Last authored field")
    )


def authored_archive():
    material = (
        text("Model colour") + text("Kit|Texture probe|71") + bytes(calcsize("<6d"))
        + pack("<i", 1) + primary_texture()
        + pack("<5i", 0, 0, 0, 0, 0) + text() + pack("<2i", 0, 1)
        + renderer() + text() + pack("<2i", 0, 0)
    )
    visual = (
        tag("moVisualProperties_c") + pack("<3I", 0, 0, 0) + material
        + text() + pack("<2i", 0, 0) + text() + pack("<6i", 0, 0, 0, 0, 0, 1) + pbr()
    )
    prefix = (
        pack("<iI", 41, 19000) + tag("moNodeName_c") + text("TextureProbe")
        + pack("<iIii", 19, 92, -5, 12) + text("Own model") + pack("<i", 0) + visual
    )
    config = tag("moPart_c") + pack("<I", len(prefix)) + prefix
    return frame_lanes({
        "Contents/Config-0": config,
        "Contents/Config-0-ModelHeader": header(("TextureProbe", "Inspection", 271), ()),
    }, 19000)


def observe_texture():
    textures = []

    def observe(frame, event, value):
        if event == "return" and frame.f_code is ReadPartVisual.__code__ and value is not None:
            textures.append(value.VisualValue.FieldsValue["f20"]["f80"])

    previous = sys.getprofile()
    sys.setprofile(observe)
    try:
        report = worker(False)
    finally:
        sys.setprofile(previous)
    require(len(textures) == 1, "primary texture lacks its single typed reader result")
    report["texture_fields"] = textures[0]
    return report


def measure():
    lookup("ascii")
    lookup("utf-16-le")
    constructing = True

    def guard(event, _):
        if constructing and (event in ("open", "os.listdir", "os.scandir", "os.system",
                                        "os.exec", "os.posix_spawn", "os.fork", "ctypes.dlopen")
                             or event.startswith(("socket.", "subprocess."))):
            raise RuntimeError("primary texture author attempted external access")

    sys.addaudithook(guard)
    try:
        raw = authored_archive()
    finally:
        constructing = False
    result = run((sys.executable, "-I", "-B", str(HERE), "--worker"), input=raw,
                 check=False, capture_output=True, timeout=50)
    require(result.returncode == 0 and not result.stderr, result.stderr.decode("utf-8"))
    report = json.loads(result.stdout)
    require(report["file_sha256"] == sha256(raw).hexdigest(), "primary texture intake changed its source")
    report["author_external_accesses"] = 0
    return report


if __name__ == "__main__":
    if sys.argv[1:] == ["--worker"]:
        report = observe_texture()
    else:
        require(not sys.argv[1:], "expected no arguments or --worker")
        report = measure()
    print(json.dumps(report, ensure_ascii=True, sort_keys=True, allow_nan=False))
