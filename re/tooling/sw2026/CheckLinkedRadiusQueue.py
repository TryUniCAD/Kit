from codecs import lookup
from dataclasses import replace
from io import BytesIO
from json import dumps
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / "src"), str(ROOT)]

from convert import open_document
from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Archive.Construction.Nodes.InitConceptMut import InitConceptMut
from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import SelfFileInput
from convert.adapters.solidworks.Archive.Construction.Part.MakeCirclePart import MakeCirclePart
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ProjectCircle import ProjectCircle
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtFormatError
from convert.adapters.solidworks.Container.Format import KPartitionStream, KResolvedFeaturesStream
from convert.adapters.solidworks.Container.Parasolid import EncodeBlank
from convert.adapters.solidworks.Core.Preparation.BindPartIntent import BindPartIntent
from convert.adapters.solidworks.Core.Preparation.MakePartRecipe import MakePartRecipe
from tests.Convert.Solidworks.CircleWriting.MakeCircleDoc import MakeCircleDoc


def require(condition, message):
    if not condition:
        raise ValueError(message)


def new_radius():
    source = MakeCircleDoc()
    (sketch,) = source.sketches
    center, diameter = sketch.constraints
    radial = source.parameter(diameter.parameter_id)
    return replace(source,
                   sketches=(replace(sketch, constraints=(center, replace(diameter, kind="radius"))),),
                   parameters=tuple(replace(row, value=replace(row.value, value=row.value.value / 2))
                                    if row.id == radial.id else row for row in source.parameters))


def incomplete_attachment(source):
    epoch = 1790000000
    plan = ProjectCircle(source)
    recipe = MakePartRecipe(plan, epoch)
    part = MakeCirclePart(source, BindPartIntent(
        source, plan, recipe, SelfFileInput(fr"C:\KitQueue\{plan.NameValue}.SLDPRT", epoch)))
    root = part.SystemValue.RootValue
    boss = part.BossValue.FeatureValue
    manager = root.FieldsValue["fd88"]
    atom_id = manager["f260"] + 1
    atom = ArchiveNode(RuntimeClass("moAtom_c", 1), {})
    InitConceptMut(atom, part.PlanValue.FeatureName)
    feature_id = boss.FieldsValue["f08"]
    tag = atom_id + 1
    atom.FieldsValue.update(f18=None, f140=atom_id, f144=0, f130=feature_id, f12c=feature_id,
                            f158=0, body_kind=0, f170=0, f18c=1, f198=-1, f180=tag, f188=1, f1b0=tag, f19c=6)
    rows = [{"o": atom}]
    manager.update(f260=atom_id, n6c=len(rows), fa8=19000, atoms=rows)
    activation = ArchiveNode(RuntimeClass("moPMarkRecord_c", 1), {"f18": 2})
    selected = ArchiveNode(RuntimeClass("moPMarkRecord_c", 1), {"f18": 4})
    root.FieldsValue.update(fe38=activation, f1010=1, nff4=1, ffe0=[{"k": atom, "v": 0}])
    boss.FieldsValue.update(has_f528=1, f528={"n": len(rows), "items": rows},
                           f498=[{"v": atom_id}], n494=1, has_f3d0=1, f3d0=selected,
                           f3c0=0, f3c8=0, f580=0, f540=3)
    config, graph = WriteConfigMut(root, 19000, part.HeaderValue)
    resolved, _ = WriteResolMut(part.ResolvedValue.RootsValue, part.ResolvedValue.ExtraFields,
                               19000, graph.MapValue, part.ResolvedValue.ContextValue)
    return BuildSldprt(dict(part.StreamsValue) | {
        "Contents/Config-0": config, KResolvedFeaturesStream: resolved,
        KPartitionStream: EncodeBlank(),
    }, FormatVersion=4)


def check():
    for encoding in ("utf-8", "utf-8-sig", "utf-16-le", "utf-16-be", "cp1252"):
        lookup(encoding)
    source = new_radius()
    source.AssertValid()
    payload = incomplete_attachment(source)
    outcomes = {}
    for with_geometry in (True, False):
        label = "geometry" if with_geometry else "design"
        options = {"source_format": "solidworks.sldprt", "include_brep": with_geometry}
        try:
            open_document(BytesIO(payload), strict=True, **options)
        except SldprtFormatError as error:
            outcomes[label] = str(error)
        else:
            raise ValueError("strict reader silently downgraded an attached radius")
        require(outcomes[label] == "active kernel transmit profile is unqualified",
                "public read stopped before it reached the attached world reader")
        doc = open_document(BytesIO(payload), strict=False, **options)
        require(any("saved circle typed owners unavailable: " + outcomes[label] == row.message
                    for row in doc.diagnostics), "permissive compatibility lost the typed refusal")
    return {"strict_refusals": outcomes, "permissive_compatibility": True}


if __name__ == "__main__":
    print(dumps(check(), sort_keys=True))
