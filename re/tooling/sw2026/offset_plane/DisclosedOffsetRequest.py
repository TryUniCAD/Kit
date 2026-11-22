from io import BytesIO

from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import (
    SelfFileInput,
)
from convert.adapters.solidworks.Archive.Construction.Geometry.DotVector import (
    DotVector,
)
from convert.adapters.solidworks.Archive.Construction.Header.HeaderInput import (
    HeaderInput,
)
from convert.adapters.solidworks.Archive.Construction.Metadata.HistoryInput import (
    HistoryInput,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.FeatureTarget import (
    FeatureTarget,
)
from convert.adapters.solidworks.Archive.Construction.OffsetPlane.OffsetFrame import (
    OffsetFrame,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartBuildInput import (
    PartBuildInput,
)
from convert.adapters.solidworks.Archive.Construction.Presentation.StyleInput import (
    StyleInput,
)
from convert.adapters.solidworks.Archive.Construction.System.PrincipalFrame import (
    PrincipalFrame,
)
from convert.adapters.solidworks.Archive.Construction.System.SystemInput import (
    SystemInput,
)
from convert.adapters.solidworks.Archive.Construction.Units.UnitInput import UnitInput
from convert.adapters.solidworks.Archive.Definition.Construction.ModelDefSettings import (
    ModelDefInput,
)

from convert.adapters.base.WriteOptions import WriteOptions
from convert.adapters.solidworks.Core.Preparation.OffsetPlane.PrepareOffPart import (
    PrepareOffPart,
)
from NeutralOffsetDocument import make_document


def prepare_disclosed(request, *, platform_views=False):
    doc = request["document"]
    pres = request["presentation"]
    prov = request["provenance"]
    style = pres["styles"]
    sc = pres["units"]
    output = request["output"]
    target = request["target"]
    offset = request["offset_plane_discovery"]
    axis = doc["plane_axis"]
    if tuple(doc["center_m"]) != (0.0, 0.0) or type(offset["reverse"]) is not bool:
        raise ValueError("offset recipe requires a centred circle and explicit reversal")
    frame = OffsetFrame(
        PrincipalFrame(axis), offset["distance_m"] * (-1 if offset["reverse"] else 1)
    )
    vector = tuple(
        a - b
        for a, b in zip(
            doc["circle_dimension"]["text_point_m"], frame.OriginValue, strict=True
        )
    )
    if DotVector(vector, frame.NormalValue) != 0:
        raise ValueError("authored radial text position does not lie on the sketch")
    document = make_document(
        {
            "name": doc["name"],
            "base": {"x": "right", "y": "top", "z": "front"}[axis],
            "plane_name": pres["plane_names"][axis],
            "datum_name": offset["name"],
            "configuration_name": doc["configuration_name"],
            "sketch_name": doc["sketch_name"],
            "boss_name": doc["extrusion_name"],
            "distance_m": offset["distance_m"],
            "reverse": offset["reverse"],
            "radius_m": doc["radius_m"],
            "depth_m": doc["depth_m"],
            "offset_unit": "m",
        }
    )
    folder_order = pres.get("folder_order", tuple(pres["folder_names"]))
    settings = PartBuildInput(
        StyleInput(
            style["standard"],
            style["font_name"],
            style["line_style_name"],
            style["language_id"],
            tuple(style["print_widths_m"]),
            tuple(style["exclusion_names"]),
            tuple(style["task_labels"]),
            tuple(style["cutlist_expressions"]),
        ),
        UnitInput(
            sc["length_unit"], sc["angle_unit"], sc["unit_system"], sc["decimal_places"]
        ),
        UnitInput("m", "radian", "mks", sc["decimal_places"]),
        SystemInput(
            tuple((name, pres["folder_names"][name]) for name in folder_order),
            tuple(pres["plane_names"].items()),
            pres["cabinet_name"],
            doc["origin_name"],
            axis,
            prov["created_at"],
            True,
        ),
        FeatureTarget(target["date_code"], target["parasolid_version"]),
        HeaderInput(
            prov["author"],
            prov["company"],
            prov["comment"],
            prov["created_at"],
            prov["modified_at"],
            prov["modified_at"],
        ),
        HistoryInput(
            prov["created_at"],
            prov["comment"],
            prov["originating_build_code"],
            prov["license_origin"],
            style["language_id"],
            pres["cjk_saved"],
        ),
        ModelDefInput(
            pres["drafting_standard"],
            tuple(pres["detail_flags"]),
            tuple(pres["tessellation"]),
            pres["system_preference_7a"],
            pres["journal_name"],
            19000,
        ),
        SelfFileInput(output["path_name"], output["saved_at"]),
        pres["hatch_name"],
        "Configurations",
        doc["density_kg_m3"],
        pres["design_intent"],
        pres["selected_leader"],
        PlatformViewMath=platform_views,
    )
    return PrepareOffPart(
        document,
        BytesIO(),
        prov["created_at"],
        WriteOptions(values={"final_destination": output["path_name"]}),
        RecipeValue=settings,
        TextPoint=(DotVector(vector, frame.AxisU), DotVector(vector, frame.AxisV)),
    )
