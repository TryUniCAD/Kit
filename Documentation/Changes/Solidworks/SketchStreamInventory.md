# SOLIDWORKS sketch stream inventory

The SOLIDWORKS reader and writer plan's repeat discovery loop starts by inventorying the streams
that carry the data for the next editable feature. This entry covers the sketch inventory for the
committed case corpora.

The inventory is [re/solidworks/SketchStreamInventory.md](../../../re/solidworks/SketchStreamInventory.md).
It lists, for the 217 committed `.SLDPRT` files under `re/solidworks/FeatureLadderRecovery/`,
`re/NativePlacement2026/Cases/` and `re/FeatureLadders2026/Cases/`, which archive streams and
native records carry sketch data, what each holds, and whether the readers under
`src/convert/adapters/solidworks/` already decode it. It also lists the exact commands used.

Findings:

- The inline sketch markup (`sgSketch`, `sgPointHandle`, `sgLineHandle`, dimensions, relations,
  display records, region and chain) lives only in the
  `Contents/Config-0-ResolvedFeatures` stream. `Contents/Config-0` carries the resolving object
  map; `swXmlContents/KeyWords` carries the feature history and its `<Dimension>` elements;
  `Contents/DisplayLists` carries only assembly tessellation; `swXmlContents/Features` is not read
  by the part reader.
- Every scoped sketch decodes as one rectangle: four lines, one point, two horizontal and two
  vertical relations, four coincident relations, and no driving sketch dimension. The only
  dimension in each file is the boss depth `D1` in the feature history.
- The external-entity proxy (`sgExtEnt_c`, `moSketchExtRef_w`, `moCompSketchEntHandle_c`) is only
  partially decoded: the reference identity is resolved, but the proxy line is emitted as raw
  native geometry rather than line geometry.
- The circle/arc records (`sgArcHandle`, `sgEntHandle`, `sgCircleDim`, `moDisplayRadialDim_c`,
  `moSkDimHandleRadial_c`) and the point-to-point distance dimensions (`sgPntPntDist`,
  `sgPntPntHorDist`, `sgPntPntVertDist`) have readers but appear in no scoped file, so their decode
  is unverified against these corpora.

Limitations and verification:

- `kit decode --layer native` does not support SOLIDWORKS (`Native decoding currently supports
  Fusion F3D only`), so the inventory uses the `container` and `neutral` layers.
- Evidence is the decode output for all 217 files (sketch provenance streams, record kinds, native
  class names, entity and constraint kinds) plus a raw byte search of the resolved stream. No
  reader was changed, so no CI-visible behaviour changed; the inventory is research evidence only
  and does not qualify any writer.
