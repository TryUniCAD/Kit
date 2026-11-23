from hashlib import sha256
from io import BytesIO
from itertools import product
from math import cos, fsum, hypot, isclose, isfinite, sin
from pathlib import Path
from xml.etree.ElementTree import fromstring
from zipfile import ZipFile
import json

SOURCE = "6f821c04ddd34092779e6781288cef62436f108dee5ff948117d35820d3d9c87"
SHAPE = "3af76e03091dcb3256e56cd1322838aadcf427859b62f6ceaf48f62ec5cb4d8a"
STOCK_RECEIPT = "b6adf8a8424a94e4869c94aae1ef1cc701da76fe8b56a053e61fe1a4e2e54101"
INVENTORY = "1de42ebe8bf52b8403de2e6a73fe45b45ac83484a6532230d4b379aff93ca03f"
NAMES = {"hinge": "Placement Hinge", "plane": "Placement Angle", "sketch": "Box001 Profile", "boss": "Box001"}
ROLES = ("Length", "Width", "Height", "Angle")
STATES = ("Original", *ROLES)
BUILD = "34.5.2.0604"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return sha256(data).hexdigest()


def wire(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode("utf-8")


def dot(first, other):
    return fsum(a * b for a, b in zip(first, other, strict=True))


def cross(first, other):
    x, y, z = first
    i, j, k = other
    return (y * k - z * j, z * i - x * k, x * j - y * i)


def add(first, other, factor=1.0):
    return tuple(a + factor * b for a, b in zip(first, other, strict=True))


def unit(value):
    size = hypot(*value)
    require(isfinite(size) and size > 0.0, "a finite nonzero hinge is required")
    return tuple(component / size for component in value)


def rotate(axis, angle, vector):
    sine, cosine = sin(angle), cos(angle)
    projection = dot(axis, vector) * (1 - cosine)
    return tuple(fsum((cosine * x, sine * y, projection * z))
                 for x, y, z in zip(vector, cross(axis, vector), axis, strict=True))


def frame(case, angle):
    return tuple(rotate(case["axis"], angle, vector)
                 for vector in ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)))


def predicted(case, state):
    require(state in STATES, "unknown disclosed source state")
    values = dict(case["original"])
    if state != "Original":
        values[state] = case["edits"][state]
    origin = case["origin_m"]
    u, v, n = frame(case, values["Angle"])
    length, width, height = (values[name] for name in ROLES[:3])
    plane = (origin, add(origin, u, length), add(add(origin, u, length), v, width),
             add(origin, v, width))
    points = (*plane, *(add(point, n, height) for point in plane))
    center = add(add(add(origin, u, length / 2), v, width / 2), n, height / 2)
    return {
        "drivers": values, "frame": (origin, u, v, n), "outline": plane,
        "vertices": points, "centroid": center, "volume": length * width * height,
        "area": 2 * (length * width + length * height + width * height),
        "bounds": tuple(op(point[axis] for point in points) for op, axis in product((min, max), range(3))),
    }


def make_case(label, origin, axis, sizes, angle, edits, source):
    return {"label": label, "cohort": "disclosed", "origin_m": tuple(origin), "axis": unit(axis),
            "original": dict(zip(ROLES, (*sizes, angle), strict=True)),
            "edits": dict(zip(ROLES, edits, strict=True)), "source": source}


def known_cases():
    factual = make_case("C057Box001", (2.0, 6.0, 0.0), (-2, 1, 0),
                        (0.2, 0.5, 0.1), 0.6405223126794245,
                        (0.219, 0.463, 0.114, 0.713),
                        {"fcstd_sha256": SOURCE, "bound_shape_sha256": SHAPE,
                         "object": "Box001", "object_id": "4972", "aliases": tuple("Box001." + x for x in ROLES[:3])})
    contrast = make_case("SignedRollContrast", (0.317, -0.021, 0.0), (1, 3, 0),
                         (0.173, 0.092, 0.054), -0.433,
                         (0.184, 0.083, 0.062, -0.509),
                         {"purpose": "independently authored signed hinge and in-plane roll contrast"})
    return json.loads(wire((factual, contrast)))


def checked(path, expected):
    require(path.is_file() and not path.is_symlink(), "expected an actual bound input file")
    data = path.read_bytes()
    require(digest(data) == expected, "input file digest differs: " + path.name)
    return data


def source_case(inventory_path, corpus_receipt):
    reference = json.loads(checked(corpus_receipt, STOCK_RECEIPT))["cases"]["C057-P01"]
    rows = json.loads(checked(inventory_path, INVENTORY))["files"]
    row, = (row for row in rows if row["case_id"] == "C057-P01")
    require(row["sha256"] == reference["source_sha256"] == SOURCE, "C057 source authority changed")
    path = Path(row["source_path"]).resolve(strict=True)
    require(path.suffix.casefold() == ".fcstd" and not any(
        value in str(path).casefold() for value in ("sealed", "heldout", "holdout")),
        "the corpus path is outside the disclosed FreeCAD case")
    raw = checked(path, SOURCE)
    case = known_cases()[0]
    with ZipFile(BytesIO(raw)) as archive:
        xml = fromstring(archive.read("Document.xml"))
        declared = xml.find("./Objects/Object[@name='Box001']")
        record = xml.find("./ObjectData/Object[@name='Box001']/Properties")
        require(declared.attrib["type"] == "Part::Box" and declared.attrib["id"] == "4972",
                "the disclosed primitive has a different owner")
        props = {field.attrib["name"]: field[0] for field in record if len(field)}
        placement = props["Placement"].attrib
        amounts = tuple(float(props[name].attrib["value"]) * 0.001 for name in ROLES[:3])
        origin = tuple(float(placement[key]) * 0.001 for key in ("Px", "Py", "Pz"))
        axis = unit(tuple(float(placement[key]) for key in ("Ox", "Oy", "Oz")))
        angle = float(placement["A"])
        require(origin == tuple(case["origin_m"]) and amounts == tuple(case["original"][name] for name in ROLES[:3])
                and all(isclose(a, b, rel_tol=0, abs_tol=1e-15) for a, b in zip(axis, case["axis"], strict=True))
                and angle == case["original"]["Angle"] and props["Label"].attrib["value"] == "Box001"
                and digest(archive.read(props["Shape"].attrib["file"])) == SHAPE,
                "the independently checked C057 inputs changed")
        source_words = tuple(float(placement[key]) for key in ("Q0", "Q1", "Q2", "Q3"))
        require(all(isclose(first, other, rel_tol=0, abs_tol=1e-14)
                    for first, other in zip(source_words, (*(part * sin(angle / 2) for part in axis), cos(angle / 2)), strict=True)),
                "FreeCAD quaternion no longer matches the independently restored signed axis-angle")
    require(checked(path, SOURCE) == raw, "C057 source changed during the host preflight")
    return case
