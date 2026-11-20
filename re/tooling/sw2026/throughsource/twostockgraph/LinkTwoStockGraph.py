from dataclasses import dataclass
from math import isclose

from convert.adapters.solidworks.Archive.Cmgr.ReadCmgrMut import ReadCmgrMut
from convert.adapters.solidworks.Archive.Cmgr.WriteCmgrMut import WriteCmgrMut
from convert.adapters.solidworks.Archive.Config.MakeLinkContext import MakeLinkContext
from convert.adapters.solidworks.Archive.Config.WriteConfigMut import WriteConfigMut
from convert.adapters.solidworks.Archive.Construction.Metadata.KeywordConfig import (
    KeywordConfig,
)
from convert.adapters.solidworks.Archive.Construction.Metadata.KeywordFeature import (
    KeywordFeature,
)
from convert.adapters.solidworks.Archive.Construction.Metadata.MakeKeywords import (
    MakeKeywords,
)
from convert.adapters.solidworks.Archive.Construction.Part.EmitPartArchive import (
    EmitPartArchive,
)
from convert.adapters.solidworks.Archive.Construction.Part.MakeCutKeys import (
    MakeCutKeys,
)
from convert.adapters.solidworks.Archive.Construction.Part.MakePartHeaders import (
    MakePartHeaders,
)
from convert.adapters.solidworks.Archive.Construction.SketchDimensions.MakeSketchKeys import (
    MakeSketchKeys,
)
from convert.adapters.solidworks.Archive.Definition.Construction.MakePartDef import (
    MakePartDef,
)
from convert.adapters.solidworks.Archive.Header.ReadNativeHeader import ReadHeaderGraph
from convert.adapters.solidworks.Archive.Header.WriteHeaderGraph import WriteHeadGraph
from convert.adapters.solidworks.Archive.Resolved.WriteResolMut import WriteResolMut
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadNodeName,
)
from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive
from convert.adapters.solidworks.Container.Format import KeywordsStream
from convert.adapters.solidworks.Core.Native import ParseKeywords
from convert.adapters.solidworks.Core.TypedResolved.Circles.ReadLocalCirc import (
    ReadLocalCirc,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.CheckCutWrapper import (
    CheckCutWrapper,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.ReadStockAtom import (
    ReadStockAtom,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.ReadStockOps import (
    ReadStockOps,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.ReadStockRoots import (
    ReadStockRoots,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.ReadCutAtomId import (
    ReadCutAtomId,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.ReadManagedCutAtoms import (
    ReadCutAtoms,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ColdOutput.CheckColdAtom import (
    CheckColdAtom,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.ReadPrismFrame import (
    ReadPrismFrame,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.Presentation.CheckTreeAlias import (
    CheckTreeAlias,
)
from convert.adapters.solidworks.Core.TypedResolved.Presentation.ReadThruStock import (
    ReadThruStock,
)
from convert.adapters.solidworks.Core.TypedResolved.ReadNativeLink import ReadNativeLink
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative

from ShapeIntent import project_intent, require


@dataclass(frozen=True)
class LinkedPart:
    streams: dict[str, bytes]
    payload: bytes

    @property
    def keywords(self):
        return self.streams[KeywordsStream]


def keyword_row(node, tag, dims=(), children=()):
    return KeywordFeature(
        FieldInt(node.FieldsValue, "f08"),
        ReadNodeName(node),
        node.ClassValue.NameValue,
        tag,
        dims,
        children,
        None,
        None,
    )


def owner_keywords(graph):
    unit = graph.settings.DocumentUnits.LengthUnit
    rows = tuple(keyword_row(node, "Feature") for node in graph.system.FeatureValues)
    for stock in graph.stocks:
        profile = stock.profile.ProfileValue
        rows += (
            keyword_row(profile, "Sketch"),
            keyword_row(
                stock.feature,
                "Extrusion",
                MakeSketchKeys((stock.driver,), unit),
                (NativeNodeId(profile),),
            ),
        )
    rows += MakeCutKeys(graph.cut, (), unit)
    configs = tuple(
        KeywordConfig(FieldInt(node.FieldsValue, "f08"), ReadNodeName(node), "")
        for node in graph.system.ConfigValues
    )
    return MakeKeywords(
        graph.selected.plan.NameValue,
        graph.settings.HeaderValue.ModifiedAt,
        configs,
        rows,
    )


def link_graph(graph):
    settings = graph.settings
    require(
        settings.TargetValue.FileVersion == 19000,
        "two stock archive requires the measured part version",
    )
    streams, _, _ = EmitPartArchive(
        graph.system,
        graph.ordered_roots,
        MakePartHeaders(graph.system, settings, graph.allocator),
        MakePartDef(settings.DefinitionValue, settings.DensityValue),
        settings,
        owner_keywords(graph),
    )
    require(
        not any("Partition" in name or "LocalBodies" in name for name in streams),
        "provisional two stock archive cannot carry cached solids",
    )
    return LinkedPart(streams, BuildSldprt(streams, FormatVersion=4))


def read_link(part):
    version = 19000
    archive = SldprtArchive.from_bytes(part.payload)
    require(
        archive.streams == part.streams, "container readback changed generated streams"
    )
    link = ReadNativeLink(archive, 0)
    streams = archive.streams
    header_name = link.ConfigName + "-ModelHeader"
    manager_name = "Contents/CMgr"
    header = ReadHeaderGraph(streams[header_name], version)
    manager = ReadCmgrMut(streams[manager_name], version)
    config, resolved = link.ConfigValue, link.ResolvedValue
    context = MakeLinkContext(config, manager)
    require(
        WriteHeadGraph(header, version) == streams[header_name]
        and WriteCmgrMut(manager.RootValue, version) == streams[manager_name]
        and WriteConfigMut(config.RootValue, version, header)[0]
        == streams[link.ConfigName]
        and WriteResolMut(
            resolved.RootsValue, resolved.ExtraFields, version, config.MapValue, context
        )[0]
        == streams[link.StreamName],
        "typed owner graph changed during the archive round trip",
    )
    return link


def read_roles(graph, link):
    root = link.ConfigValue.RootValue
    features = ReadStockRoots(link)
    first, second, cut = ReadStockOps(link, features)
    atoms = (
        ReadStockAtom(first.NodeValue, False),
        ReadStockAtom(second.NodeValue, False),
    )
    require(
        set(atoms) == ReadCutAtoms(link) and len(set(atoms)) == 2,
        "independent stock outputs differ from the actual two manager atoms",
    )
    ids = tuple(
        ReadCutAtomId(atom, owner.NodeValue)
        for atom, owner in zip(atoms, (first, second), strict=True)
    )
    require(
        len(set(ids)) == 2 and root.FieldsValue["fd88"]["f260"] == ids[-1],
        "stock atom identities do not follow their independent allocator",
    )
    for atom in atoms:
        CheckColdAtom(atom, ImplicitName=True)
    selected = next(
        index for index, stock in enumerate(graph.stocks) if stock is graph.selected
    )
    CheckCutWrapper(
        root,
        (first, second)[selected].NodeValue,
        cut.NodeValue,
        ids[selected],
        IsCold=True,
    )
    cut_fields = cut.NodeValue.FieldsValue
    require(
        cut_fields["f544"] == cut_fields["has_f548"] == 1
        and not any(
            cut_fields[key]
            for key in ("has_f528", "has_f530", "has_f4c0", "has_f4a8", "has_f4b0")
        ),
        "pre-rebuild cut has an unproven result or chooser owner",
    )
    CheckTreeAlias(
        link,
        (
            root,
            *(owner.NodeValue for owner in (first, second, cut)),
            *(owner.ProfileValue for owner in (first, second, cut)),
            *atoms,
        ),
    )
    return features, (first, second, cut), ids, selected


def verify_link(graph, link, keywords):
    features, owners, ids, selected = read_roles(graph, link)
    first, second, cut = owners
    intent = project_intent(graph.document)
    authored = {
        stock.feature_id: stock for stock in (intent.selected, intent.untouched)
    }
    root = link.ConfigValue.RootValue
    read_frames = tuple(
        ReadPrismFrame(owner.ProfileValue, root, features, FrontOnly=False)
        for owner in owners
    )
    wanted_frames = tuple(
        authored[stock.plan.FeatureId].frame for stock in graph.stocks
    )
    require(
        read_frames == (*wanted_frames, wanted_frames[selected]),
        "linked profiles lost their actual support frames",
    )
    circle_node = RequireNative(cut.ProfileValue.FieldsValue.get("pd_f80"), "sgSketch")
    circle = ReadLocalCirc(circle_node, link, AllowFree=True)
    require(
        circle is not None
        and circle[1] is None
        and all(
            isclose(a, b, rel_tol=1e-13, abs_tol=1e-12)
            for a, b in zip(
                (*circle[0].CenterValue, circle[0].RadiusValue),
                (intent.circle.center.x, intent.circle.center.y, intent.circle.radius),
                strict=True,
            )
        ),
        "linked selected tool differs from its actual neutral circle",
    )
    cfgs, rows = ParseKeywords(keywords)
    require(
        len(cfgs) == 1 and cfgs[0].name == graph.document.configurations[0].name,
        "keywords lost the actual neutral configuration",
    )
    by_id = {row.object_id: row for row in rows}
    unit_scale = {"mm": 0.001, "m": 1.0, "in": 0.0254}[
        graph.settings.DocumentUnits.LengthUnit
    ]
    results = []
    for owner, stock, frame, atom_id in zip(
        (first, second), graph.stocks, read_frames[:2], ids, strict=True
    ):
        node_id = NativeNodeId(owner.NodeValue)
        depth = owner.RequireDepth().DepthValue
        loop = ReadThruStock(owner.ProfileValue, link)
        points = tuple(
            sorted(point.PositionValue for point in loop.PointsValue.values())
        )
        expected = tuple(
            sorted(
                (point.x, point.y) for point in authored[stock.plan.FeatureId].corners
            )
        )
        dimensions = by_id[node_id].dimensions
        require(
            depth.name == "D1"
            and by_id[node_id].name == stock.plan.FeatureName
            and len(dimensions) == 1
            and dimensions[0].name == "D1"
            and dimensions[0].kind == "length"
            and isclose(
                dimensions[0].value_mm * unit_scale,
                stock.plan.DepthValue,
                rel_tol=1e-9,
                abs_tol=1e-12,
            )
            and isclose(
                depth.native_value, stock.plan.DepthValue, rel_tol=1e-13, abs_tol=1e-15
            )
            and all(
                isclose(a, b, rel_tol=1e-13, abs_tol=1e-12)
                for first_point, second_point in zip(points, expected, strict=True)
                for a, b in zip(first_point, second_point, strict=True)
            ),
            "actual linked stock dimension or contour differs from the authored geometry",
        )
        results.append(
            {
                "feature_id": node_id,
                "profile_id": NativeNodeId(owner.ProfileValue),
                "feature_name": ReadNodeName(owner.NodeValue),
                "native_class": owner.NodeValue.ClassValue.NameValue,
                "f810": owner.NodeValue.FieldsValue["f810"],
                "archive_atom_id": atom_id,
                "depth_m": depth.native_value,
                "d1_id": depth.TypedOwner["dimension_id"],
                "signed_normal": (frame.z_axis.x, frame.z_axis.y, frame.z_axis.z),
            }
        )
    cut_id = NativeNodeId(cut.NodeValue)
    require(
        by_id[cut_id].name == ReadNodeName(cut.NodeValue)
        and not by_id[cut_id].dimensions,
        "depthless cut acquired a keyword distance",
    )
    return results, {
        "feature_id": cut_id,
        "profile_id": NativeNodeId(cut.ProfileValue),
        "selected_feature_id": results[selected]["feature_id"],
        "selected_atom_id": ids[selected],
        "scope": cut.NodeValue.FieldsValue["f544"],
        "f810": cut.NodeValue.FieldsValue["f810"],
        "result_and_chooser_state": "pending_native_regeneration",
    }
