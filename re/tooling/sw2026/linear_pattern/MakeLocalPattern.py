from dataclasses import dataclass

from convert.adapters.solidworks.Archive.Construction.BodyScope.BindStockMut import BindStockMut
from convert.adapters.solidworks.Archive.Construction.Configuration.SetCfgStampMut import SetCfgStampMut
from convert.adapters.solidworks.Archive.Construction.Nodes.AtomSeeds import KAtomLists, KAtomWords
from convert.adapters.solidworks.Archive.Construction.Nodes.InitFeatureMut import InitFeatureMut
from convert.adapters.solidworks.Archive.Construction.Patterns.Direction.MakePatDir import MakePatDir
from convert.adapters.solidworks.Archive.Construction.Patterns.Direction.ReadPatDir import ReadPatDir
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import ReadNodeName

from CheckPatternAngleOwners import point as read_point, require
from MakeLocalPatternDrivers import check_styles, make_drivers
from MakePatternAngularPlane import AngularPlaneIntent, make_angular_plane_mut, typed_node
from MakePatternAnnotationCatalog import add_catalog_mut
from MakePatternHingeAxis import make_hinge_mut
from MakePatternPrincipalDisplay import point
from MakePatternSeed import RaisedSeedGraph, RaisedSeedIntent, bind_plate_lineage_mut, make_raised_seed
from PatternAngleGeometry import offsets
from PatternBoxGeometry import whole_solid_measure
from PatternHingeGeometry import ORIGIN


@dataclass(frozen=True, slots=True)
class LocalPatternIntent:
    name: str
    count: int
    pitch_m: float
    reverse: bool
    styles: tuple


@dataclass(frozen=True, slots=True)
class PatternGraph:
    seed: RaisedSeedGraph
    axis: object
    plane: object
    plane_driver: object
    pattern: object
    pattern_drivers: tuple
    headers: tuple
    measure: dict

    @property
    def roots(self):
        return (*self.seed.roots, self.axis, self.plane, self.pattern)


def empty_items():
    return {"n": 0, "items": []}


def original_owner():
    return {
        "f00": 1, "f08": None, "has_f10": 0, "f18": 0, "f20": 0.0,
        "fb4": 0, "fb8": 0.0, "fc0": 0.0, "f260": 0, "fc8": -1, "fcc": -1, "fd0": 0,
        "fd4": 0, "f1d8": 0, "f1d0": 0, "f1d4": 0, "f218": -1, "has_f228": 0,
        "n1e0": 0, "f1e0": [], "f1c0": 0, "f1b0": empty_items(), "f25c": 0,
    }


def initial_pattern(seed, name):
    pattern = typed_node("moLPattern_c", {})
    InitFeatureMut(pattern, name, seed.system.RootValue, seed.settings.TargetValue)
    fields = pattern.FieldsValue
    fields.update(dict.fromkeys(KAtomWords, 0))
    fields.update({key: [] for key in KAtomLists})
    fields.update(f35c=0, f368=empty_items(), f388=empty_items(), f538=None, f4a0=1,
                  f6e0=None, f758=None, f780=empty_items(), f7a0=0)
    fields.update(dict.fromkeys(("f820", "f8e0", "f950", "f1278", "f1280", "f1290", "f12e8", "f12f0", "f1300", "f1308")))
    fields.update(dict.fromkeys(("fa00", "f948", "n870", "nf30", "fa04", "fa08", "na10", "na30", "f1128", "n930",
                                 "f112c", "f129c", "f12a4", "f12e0", "f12e4", "f1310", "f1314", "f1328", "f132c", "f12a0"), 0))
    fields.update(dict.fromkeys(("f9e0", "f9fc", "f1050", "f1130", "f12f8", "f12fc"), 1))
    fields.update(f9f0=0, f1054=0, f870=[], f930=[], f840=empty_items(), ff50=empty_items(), f8e8=empty_items(),
                  ffa0={"f30": 1, "f48": None, "f98": 0, "f68": None, "f18": point(ORIGIN), "f9c": 0},
                  fa50=original_owner(), fcb8=original_owner())
    fields.update({key: typed_node("suObList", empty_items()) for key in ("f9d8", "f8d8", "f990")})
    fields["f988"] = typed_node("suObList", {"n": 1, "items": [{"o": seed.seed.FeatureValue}]})
    return pattern


def direction_fields(plane):
    line = ReadPatDir(plane)
    return {"fc8": line.PointValue, "fe0": line.DirectionValue, "fb0": 0.0, "fb8": line.SpanValue, "f68": 1}


def direction_node(seed, plane, headers, line):
    wrapper = MakePatDir(seed.system, seed.settings, seed.allocator, plane, (headers[0], headers[1]))
    fields = wrapper.FieldsValue
    require(line == {"fc8": read_point(fields["fc8"]), "fe0": read_point(fields["fe0"]),
                     "fb0": fields["fb0"], "fb8": fields["fb8"], "f68": fields["f68"]},
            "selected direction fields differ from the actual generated plane")
    return wrapper


def make_pattern(seed_intent, axis_name, plane_intent, annotation, pattern_intent):
    require(type(seed_intent) is RaisedSeedIntent and type(plane_intent) is AngularPlaneIntent
            and type(pattern_intent) is LocalPatternIntent and type(pattern_intent.reverse) is bool,
            "pattern requires explicit raised seed, angle constraint and signed repetition intent")
    check_styles(pattern_intent.styles)
    seed = make_raised_seed(seed_intent)
    labels = (*map(ReadNodeName, seed.roots), axis_name, plane_intent.name, pattern_intent.name)
    require(all(type(name) is str and name and name.isprintable() for name in labels) and len(set(labels)) == len(labels),
            "pattern feature, hinge and plane labels must be distinct actual native names")
    system = seed.system
    axis, initial = make_hinge_mut(system, seed.settings, seed.allocator, axis_name, seed.bounds_m)
    add_catalog_mut(system.RootValue, annotation["views"], annotation["active"], annotation["shown"], version=19000)
    plane, plane_driver, plane_headers = make_angular_plane_mut(system, seed.settings, seed.allocator, axis, initial, plane_intent)
    line = direction_fields(plane)
    direction = tuple(-value if pattern_intent.reverse else value for value in line["fe0"])
    model_measure = whole_solid_measure(seed_intent.plate.bounds_m, seed_intent.seed.bounds_m, direction,
                                        pattern_intent.pitch_m, pattern_intent.count)
    start = tuple(map(float, seed_intent.seed.bounds_m[0]))
    finish = offsets(start, direction, pattern_intent.pitch_m)
    pattern = initial_pattern(seed, pattern_intent.name)
    drivers = make_drivers(pattern, system.RootValue, pattern_intent.styles, pattern_intent.count,
                           pattern_intent.pitch_m, (start, finish), seed.allocator)
    seed.allocator.AllocateMut(pattern)
    pattern.FieldsValue.update(f1288=direction_node(seed, plane, plane_headers, line), f1298=int(pattern_intent.reverse))
    result = BindStockMut(system.RootValue.FieldsValue["fd88"], pattern, AppendMember=True)
    plate_operation, seed_operation = seed.plate, seed.seed
    bind_plate_lineage_mut(system.RootValue, seed_operation.FeatureValue, seed_operation.AtomValue, pattern, result,
                           prior=((plate_operation.FeatureValue, plate_operation.AtomValue),))
    pattern.FieldsValue["f9f0"] = 1
    SetCfgStampMut(system.ConfigValues[0], seed.allocator)
    return PatternGraph(seed, axis, plane, plane_driver, pattern, drivers, seed.headers(axis, plane, pattern), model_measure)
