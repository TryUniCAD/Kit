from convert.adapters.solidworks.Archive.Construction.Views.Annotations.AnnoViewInput import (
    AnnoViewInput,
    KNoAnno as UNASSIGNED_ANNOTATIONS,
)
from convert.adapters.solidworks.Archive.Construction.Views.Annotations.MakeAnnoView import (
    KAnnoWorld as WORLD,
    MakeAnnoFrame,
    MakeAnnoView,
    ReadAnnoBasis,
)
from convert.adapters.solidworks.Archive.Construction.Views.Annotations.PutAnnoCatalog import (
    PutAnnoCatalog,
)
from convert.adapters.solidworks.Archive.Construction.Views.Annotations.ReadAnnoView import (
    ReadAnnoView,
)


def annotation_frame(value):
    return MakeAnnoFrame(value)


def annotation_node(name, basis, identity):
    return MakeAnnoView(AnnoViewInput(name, ReadAnnoBasis(basis)), identity)


def annotation_inputs(intents):
    if not isinstance(intents, (tuple, list)):
        raise ValueError("expected an ordered bounded catalog and explicit shown view roles")
    if any(type(intent) is not dict or set(intent) != {"name", "basis"} for intent in intents):
        raise ValueError("unknown authored annotation view fields")
    return tuple(AnnoViewInput(intent["name"], ReadAnnoBasis(intent["basis"])) for intent in intents)


def add_catalog_mut(model, intents, active, shown, *, version):
    if not isinstance(shown, (tuple, list)):
        raise ValueError("expected an ordered bounded catalog and explicit shown view roles")
    return PutAnnoCatalog(model, version, annotation_inputs(intents), active, tuple(shown))


def display_membership(model, name):
    view = ReadAnnoView(model, name)
    return {"n2b0": 1, "f2b0": ({"v": view.FieldsValue["f360"]},)}
