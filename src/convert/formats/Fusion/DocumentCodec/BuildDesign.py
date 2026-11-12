from convert.formats.Fusion.DocumentCodec.CheckDocSpec import CheckDocSpec
from convert.formats.Fusion.DocumentCodec.Defaults.BaseDefaults import BaseDefaults
from convert.formats.Fusion.DocumentCodec.Defaults.ExtrudeDefaults import (
    ExtrudeDefaults,
)
from convert.formats.Fusion.DocumentCodec.Defaults.SketchDefaults import SketchDefaults
from convert.formats.Fusion.DocumentCodec.Extrusion.AddExtrudeMut import AddExtrudeMut
from convert.formats.Fusion.DocumentCodec.Extrusion.BindParamsMut import BindParamsMut
from convert.formats.Fusion.DocumentCodec.Extrusion.LinkBodyMut import LinkBodyMut
from convert.formats.Fusion.DocumentCodec.Extrusion.LinkExtrudeMut import LinkExtrudeMut
from convert.formats.Fusion.DocumentCodec.Extrusion.LinkProfileMut import LinkProfileMut
from convert.formats.Fusion.DocumentCodec.Foundation.AddCollectMut import AddCollectMut
from convert.formats.Fusion.DocumentCodec.Foundation.AddComputeMut import AddComputeMut
from convert.formats.Fusion.DocumentCodec.Foundation.AddGeometryMut import (
    AddGeometryMut,
)
from convert.formats.Fusion.DocumentCodec.Foundation.AddRootsMut import AddRootsMut
from convert.formats.Fusion.DocumentCodec.Foundation.AddUnitsMut import AddUnitsMut
from convert.formats.Fusion.DocumentCodec.Foundation.LinkCompMut import LinkCompMut
from convert.formats.Fusion.DocumentCodec.Foundation.LinkRootsMut import LinkRootsMut
from convert.formats.Fusion.DocumentCodec.Model.CreateAuthor import CreateAuthor
from convert.formats.Fusion.DocumentCodec.Model.DesignResult import DesignResult
from convert.formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from convert.formats.Fusion.DocumentCodec.Records.EmitDesign import EmitDesign
from convert.formats.Fusion.DocumentCodec.Sketch.AddCircleMut import AddCircleMut
from convert.formats.Fusion.DocumentCodec.Sketch.LinkCircleMut import LinkCircleMut
from convert.formats.Fusion.SegmentCodec.Features.Binary.CheckUuid import CheckUuid


def BuildDesign(SpecValue: DocumentSpec, AssetId: str) -> DesignResult:
    CheckDocSpec(SpecValue)
    CheckUuid(AssetId)
    Author = CreateAuthor(SpecValue, AssetId)
    Author.Defaults.update(BaseDefaults())
    for Builder in (
        AddRootsMut,
        AddCollectMut,
        AddComputeMut,
        AddGeometryMut,
        AddUnitsMut,
        LinkCompMut,
        LinkRootsMut,
    ):
        Builder(Author)
    if SpecValue.ProfileKind in ("circle", "extrusion"):
        Author.Defaults.update(SketchDefaults())
        AddCircleMut(Author)
        LinkCircleMut(Author)
    if SpecValue.ProfileKind == "extrusion":
        Author.Defaults.update(ExtrudeDefaults())
        for Builder in (
            AddExtrudeMut,
            BindParamsMut,
            LinkProfileMut,
            LinkExtrudeMut,
            LinkBodyMut,
        ):
            Builder(Author)
    return EmitDesign(Author)
