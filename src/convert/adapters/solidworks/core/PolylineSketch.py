from __future__ import annotations

from interchange import (
    GeometryKind as GeomKind,
    LineGeometry as LineGeom,
    Provenance,
    ProvenanceSpan,
    SketchEntity,
    Vector2 as VectorTwo,
    frozen_mapping as FrozenMapping,
)

from .Native import NativeProfile, NativeSketch


def MapPolyline(
    Sketch: NativeSketch, ProfileIndex: int, Profile: NativeProfile
) -> tuple[list[SketchEntity], dict[str, str], dict[int, str]]:
    Coordinates = Profile.native_coordinates_mm or Profile.coordinates
    Vertices = tuple(zip(Coordinates[::2], Coordinates[1::2], strict=True))
    Entities: list[SketchEntity] = []
    RefMap: dict[str, str] = {}
    ProfileEntities: dict[int, str] = {}
    for EdgeIndex, (Start, EndValue) in enumerate(
        zip(Vertices, Vertices[1:] + Vertices[:1], strict=True)
    ):
        EntityId = (
            f"sldprt:sketch:{Sketch.object_id}:profile:{ProfileIndex}:edge:{EdgeIndex}"
        )
        MarkerOffset = (
            Profile.marker_offsets[EdgeIndex]
            if EdgeIndex < len(Profile.marker_offsets)
            else None
        )
        Source = (
            Provenance(
                adapter="solidworks.sldprt",
                native_id=f"{Sketch.object_id}:{MarkerOffset}",
                spans=(
                    ProvenanceSpan(
                        Sketch.native_stream,
                        MarkerOffset,
                        92,
                        "sketch-profile-line",
                    ),
                ),
            )
            if MarkerOffset is not None
            else Provenance(
                adapter="solidworks.sldprt",
                native_id=str(Sketch.object_id),
                spans=(
                    ProvenanceSpan(
                        Sketch.native_stream,
                        Sketch.native_offset,
                        Sketch.native_end - Sketch.native_offset,
                        "sketch-record",
                    ),
                ),
            )
        )
        Entities.append(
            SketchEntity(
                id=EntityId,
                kind=GeomKind.LINE,
                geometry=LineGeom(VectorTwo(*Start), VectorTwo(*EndValue)),
                provenance=Source,
                attributes=FrozenMapping(
                    {"profile_index": ProfileIndex, "edge_index": EdgeIndex}
                ),
            )
        )
        RefMap[
            f"{Sketch.object_id}:profile:{ProfileIndex}:edge:{EdgeIndex}"
        ] = EntityId
        if MarkerOffset is not None:
            ProfileEntities[MarkerOffset] = EntityId
    return (Entities, RefMap, ProfileEntities)
