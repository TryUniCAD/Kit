from argparse import ArgumentParser
from codecs import lookup
from hashlib import sha256
import json
from pathlib import Path
from struct import pack
from subprocess import check_output
import sys

HERE = Path(__file__).resolve()
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "src"))

from convert.adapters.solidworks.Archive.Definition.Construction.MakePartDef import MakePartDef
from convert.adapters.solidworks.Archive.Definition.Construction.ModelDefSettings import ModelDefInput
from convert.adapters.solidworks.Archive.Definition.ReadModelDef import ReadModelDef
from convert.adapters.solidworks.Archive.Definition.WriteModelDef import WriteModelDef
from convert.adapters.solidworks.Archive.Views.ReadPartView import ReadPartView
from convert.adapters.solidworks.Container.Archive import ContainerMo
from convert.adapters.solidworks.Container.Container import SldprtArchive

VERSION = 19000
IDENTITY = (1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0)
ROTATION = (0.0, -1.0, -0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0)
SHIFT = (-0.0, 0.03125, -0.125)
SCALE = 0.625
CONTROLS = {
    "ladder": (
        "ladder/L1_boss.SLDPRT",
        "55e5a9840cc78a1d4b3ac4b8de3f37540695494e4d7a0edfb3cd3a2a876e2ac6",
        "14d9b75edf4586f8e1db2b166e855e29a03d4c88256e26d24351edb5c43d8a87",
        (0.8844181216774213, -0.24036589468392133, 0.400036026779314,
         1.3877787807814457e-17, 0.8571673007021341, 0.5150380749100181,
         -0.4666953889300622, -0.4555090068042732, 0.7580942940502868),
        (0.03490443496581813, 0.01343819220345903, -0.022364907564101685),
        5.900297031550575, 1, 1,
    ),
    "one_light": (
        "light-counts/OneLights.SLDPRT",
        "b2772eebfd9f11038f72c76fe3a6ace4b9cd45373425f75921be45174943edb7",
        "967533dc08fd32608fb231adca3e6a1ac42533fbaa93491f90dce8911384fcb7",
        IDENTITY, (0.010505988556330606, 0.008014596837307151, 0.0),
        3.3533877980364655, 1, 0,
    ),
    "local": (
        "local-import-readback/ConcaveOwned.SLDPRT",
        "fa1b84b7cd9e8860d549c599fdb536c6de965e3ec7b4ed5f53706cb57c743d33",
        "2381c1a45d1554608019d81fd151ee7ee2fb9d43c1ef6ab2b988892cc5130dfd",
        IDENTITY, (0.0, 0.0, 0.0), 1.0, 0, 0,
    ),
}
MODE_ERROR = "source camera requires ordinary orthographic transform modes"
AFFINE_ERROR = "source camera contains unrepresented affine state"
REFUSALS = {
    "perspective": MODE_ERROR,
    "pan_matrix": MODE_ERROR,
    "model_pan": AFFINE_ERROR,
    "model_negative_zero": AFFINE_ERROR,
    "explicit_identity": "source camera matrix presence cannot be regenerated",
    "reflection": "view rotation must preserve orientation",
    "shear": "view rotation rows must be orthonormal",
    "zero_scale": "view scale must be positive",
    "nan_pan": "view coordinate or scale must be finite",
    "infinite_zoom": "view coordinate or scale must be finite",
    "infinite_matrix": "view coordinate or scale must be finite",
}


def guard():
    for codec in ("ascii", "utf-16-le", "latin-1", "cp1252"):
        lookup(codec)
    attempts = []

    def deny(event, args):
        if event in {"open", "socket.connect", "subprocess.Popen", "os.system", "os.exec",
                     "os.posix_spawn", "ctypes.dlopen"}:
            attempts.append(event)
            raise PermissionError(f"unexpected saved view access {event}")

    sys.addaudithook(deny)
    return attempts


def digest(data):
    return sha256(data).hexdigest()


def pose_bits(matrix, translation, scale):
    return pack("<13d", *matrix, *translation, scale)


def inspect_view(data, version, expected):
    actual = ReadPartView(data, version)
    measured = pose_bits(actual.MatrixValues, actual.ShiftValues, actual.ScaleValue)
    assert measured == pose_bits(*expected)
    read = ReadModelDef(data, version)
    assert WriteModelDef(read.GraphValue).OutputValue == data
    fields = read.GraphValue.DocumentValue.FieldsValue
    return {"definition_bytes": len(data), "definition_sha256": digest(data), "pose_sha256": digest(measured),
            "matrix": actual.MatrixValues, "pan": actual.ShiftValues, "scale": actual.ScaleValue,
            "matrix_present": fields["fae8"]["has_matrix"], "user_environments": fields["nenv"],
            "definition_map_counter": read.MapValue.CounterValue}


def source_case(case):
    name, source_hash, def_hash, matrix, pan, zoom, environment, presence = CONTROLS[case]
    path = Path("re/solidworks/v2026/corpus") / name
    source = (ROOT / path).read_bytes()
    assert digest(source) == source_hash
    attempts = guard()
    arc = SldprtArchive.from_bytes(source)
    version = ContainerMo(arc.streams)
    definition = arc.require("Contents/Definition")
    assert arc.format_version == 4 and version == VERSION and digest(definition) == def_hash
    result = inspect_view(definition, version, (matrix, pan, zoom))
    assert (result["user_environments"], result["matrix_present"]) == (environment, presence)
    assert not attempts
    return {**result, "source_sha256": source_hash, "source_path": path.as_posix()}


def coefficients(matrix):
    return {f"m{index}": value for index, value in enumerate(matrix)}


def wire(case):
    settings = ModelDefInput("moISO_c", (2, 17), (26, 4, 25, True), False, "SavedPose", VERSION)
    graph = MakePartDef(settings, 1000.0)
    fields = graph.DocumentValue.FieldsValue
    model = {"has_matrix": 1, "f08": coefficients(ROTATION),
             "f58": 0.0, "f60": 0.0, "f68": 0.0, "f70": 1.0, "f78": 0}
    pan = {"has_matrix": 0, "f58": SHIFT[0], "f60": SHIFT[1], "f68": SHIFT[2],
           "f70": SCALE, "f78": 0}
    if case == "perspective":
        model.update(f78=32, f80={"f08": 0.2, "f10": 0.3, "f18": 0.4, "f20": 0.5,
                                "f28": 0.6, "f30": 0.7})
    elif case == "pan_matrix":
        pan.update(has_matrix=1, f08=coefficients(ROTATION))
    elif case == "model_pan":
        model["f60"] = 0.125
    elif case == "model_negative_zero":
        model["f58"] = -0.0
    elif case == "explicit_identity":
        model["f08"] = coefficients(IDENTITY)
    elif case == "reflection":
        model["f08"] = coefficients(tuple(-value if index < 3 else value
                                         for index, value in enumerate(ROTATION)))
    elif case == "shear":
        model["f08"]["m1"] = -0.75
    elif case == "zero_scale":
        pan["f70"] = 0.0
    elif case == "nan_pan":
        pan["f58"] = float("nan")
    elif case == "infinite_zoom":
        pan["f70"] = float("inf")
    elif case == "infinite_matrix":
        model["f08"]["m8"] = float("-inf")
    fields.update(fae8=model, faf0=pan)
    return WriteModelDef(graph).OutputValue


def author():
    attempts = guard()
    outputs = {case: wire(case).hex() for case in ("rotation", *REFUSALS)}
    assert not attempts
    return outputs


def refuse(data, version, expected):
    try:
        ReadPartView(data, version)
    except ValueError as error:
        assert str(error) == expected, str(error)
        return str(error)
    raise AssertionError(f"saved view inspection accepted {expected}")


def inspect(issued):
    attempts = guard()
    data = bytes.fromhex(issued["rotation"])
    positive = inspect_view(data, VERSION, (ROTATION, SHIFT, SCALE))
    failures = {}
    for name, expected in REFUSALS.items():
        altered = bytes.fromhex(issued[name])
        graph = ReadModelDef(altered, VERSION).GraphValue
        assert WriteModelDef(graph).OutputValue == altered
        failures[name] = refuse(altered, VERSION, expected)
    failures["wrong_version"] = refuse(b"", 18900, "SOLIDWORKS model Definition requires archive version 19000")
    failures["trailing"] = refuse(data + b"\0", VERSION, "SOLIDWORKS model Definition has an unconsumed tail")
    assert not attempts
    return {"analytic": positive, "refusals": failures}


def measure():
    start = (sys.executable, "-I", "-B", str(HERE))
    issued = check_output((*start, "author"), timeout=45)
    authored = json.loads(check_output((*start, "inspect"), input=issued, timeout=45))
    samples = {case: json.loads(check_output((*start, case), timeout=45)) for case in CONTROLS}
    return {**authored, "sources": samples, "guarded_processes": 2 + len(CONTROLS), "runtime_external_accesses": 0}


def main():
    parser = ArgumentParser(description="Inspect the saved SOLIDWORKS part Definition view pair")
    parser.add_argument("case", choices=("measure", "author", "inspect", *CONTROLS))
    case = parser.parse_args().case
    if case == "measure":
        result = measure()
    elif case == "author":
        result = author()
    elif case == "inspect":
        result = inspect(json.load(sys.stdin))
    else:
        result = source_case(case)
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
