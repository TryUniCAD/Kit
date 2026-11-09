---
title: "FreeCAD Format Adapter"
wiki_page_id: "page-adapter-freecad"
---

<details>
<summary>Relevant source files</summary>

The following files were used as context for generating this wiki page:

- [src/convert/adapters/freecad/Adapter.py](src/convert/adapters/freecad/Adapter.py)
- [src/convert/adapters/freecad/Archive.py](src/convert/adapters/freecad/Archive.py)
- [src/convert/adapters/freecad/Brep.py](src/convert/adapters/freecad/Brep.py)
- [src/convert/adapters/freecad/Native.py](src/convert/adapters/freecad/Native.py)
- [src/convert/adapters/freecad/Protocol.py](src/convert/adapters/freecad/Protocol.py)
- [tests/convert/freecad/FreecadTests.py](tests/convert/freecad/FreecadTests.py)
</details>

# FreeCAD Format Adapter

The FreeCAD Format Adapter is a core component of the Kit interchange system. It provides bidirectional translation between FreeCAD's native `.FCStd` format and the neutral Kit `CadDocument` model. The adapter operates by directly parsing and generating FreeCAD ZIP-based archives without requiring a FreeCAD installation or vendor runtime.

Sources: [src/convert/adapters/freecad/Adapter.py:1082-1111](src/convert/adapters/freecad/Adapter.py#L1082-L1111), [README.md:27-31](README.md#L27-L31)

## Architecture Overview

The adapter follows a layered architecture to handle the complexities of the FreeCAD file format. It decomposes the conversion process into archive handling, object graph parsing, and geometry reconstruction.

```mermaid
flowchart TD
    Source[Source .FCStd] --> Archive[Archive Layer]
    Archive --> XML[Document.xml Parser]
    XML --> Graph[Object Graph]
    Graph --> Translator[Adapter Translator]
    Translator --> Neutral[CadDocument]
    
    Neutral --> Builder[Rebuild / Replay Logic]
    Builder --> ArchiveOut[Archive Builder]
    ArchiveOut --> Destination[.FCStd Output]
```

The diagram above shows the data flow from a native FreeCAD file through the parsing layers to a neutral document, and the subsequent path back to a generated FreeCAD file.
Sources: [src/convert/adapters/freecad/Adapter.py:1082-1111](src/convert/adapters/freecad/Adapter.py#L1082-L1111), [src/convert/adapters/freecad/Native.py:1052-1147](src/convert/adapters/freecad/Native.py#L1052-L1147)

### Component Roles

| Component | Responsibility |
| :--- | :--- |
| `FreeCadAdapter` | Entry point implementing `probe`, `read`, and `write` interfaces. |
| `Archive.py` | Handles ZIP structure, resource limits, and XML extraction. |
| `Native.py` | Decodes native FreeCAD object graphs, sketches, and features. |
| `Brep.py` | Translates OpenCASCADE B-Rep data between FreeCAD and neutral models. |
| `Protocol.py` | Defines type IDs, constraint codes, and feature family mappings. |

Sources: [src/convert/adapters/freecad/Adapter.py:1082-1111](src/convert/adapters/freecad/Adapter.py#L1082-L1111), [src/convert/adapters/freecad/Archive.py:122-156](src/convert/adapters/freecad/Archive.py#L122-L156), [src/convert/adapters/freecad/Native.py:53-73](src/convert/adapters/freecad/Native.py#L53-L73)

## Archive Handling

FreeCAD files are ZIP archives containing a primary `Document.xml` and auxiliary sidecar files like `.brp` (OpenCASCADE B-Rep) or `.bms` (Binary Mesh). The adapter enforces strict security and resource limits during archive extraction to prevent exploits like compression bombs or unsafe path traversals.

Sources: [src/convert/adapters/freecad/Archive.py:122-156](src/convert/adapters/freecad/Archive.py#L122-L156)

### Resource Limits

| Limit | Value | Description |
| :--- | :--- | :--- |
| `MAX_ENTRY_SIZE` | 512 MB | Maximum size of a single file within the archive. |
| `MAX_TOTAL_SIZE` | 1024 MB | Maximum aggregate size of all entries. |
| `MAX_ENTRIES` | 16,384 | Maximum number of files in one archive. |
| `MAX_COMPRESSION_RATIO` | 500 | Prevents "ZIP bomb" attacks. |

Sources: [src/convert/adapters/freecad/Archive.py:61-75](src/convert/adapters/freecad/Archive.py#L61-L75)

## Object Graph Translation

The adapter parses the `Document.xml` to reconstruct the parametric history. It maps native FreeCAD types to neutral `FeatureKind` and `GeometryKind` enums.

### Supported Feature Types

The adapter recognizes over 90 native feature types. Key families include:
- **PartDesign**: Pads, Pockets, Revolutions, Grooves, Fillets, Chamfers.
- **App**: Planes, Links, Parts.
- **Assembly**: Assembly Objects, Joint Groups, Joints.

Sources: [src/convert/adapters/freecad/Protocol.py](src/convert/adapters/freecad/Protocol.py) (FeatureTypes and family mappings), [src/convert/adapters/freecad/Native.py:734-754](src/convert/adapters/freecad/Native.py#L734-L754)

### Sketch and Constraint Parsing

Native sketches are translated by mapping `Sketcher::PropertyConstraintList` to neutral `SketchConstraint` objects.

```mermaid
sequenceDiagram
    participant N as Native Sketch
    participant G as Geometry Parser
    participant C as Constraint Resolver
    participant I as Interchange Model
    N->>G: Extract PropertyGeometryList
    G-->>N: Resolve Point/Line/Circle/Conic/Spline
    N->>C: Extract PropertyConstraintList
    C->>C: Map Code (e.g., 1=Coincident)
    C->>C: Resolve Entity Indices to IDs
    C-->>N: Build Neutral Constraints
    N->>I: Assemble SketchData
```

Sources: [src/convert/adapters/freecad/Native.py:587-634](src/convert/adapters/freecad/Native.py#L587-L634), [src/convert/adapters/freecad/Native.py:657-695](src/convert/adapters/freecad/Native.py#L657-L695)

## Write Logic: Rebuild vs. Replay

The adapter implements two distinct write strategies: **Exact Replay** and **Reconstruction**.

### Exact Replay
If the `CadDocument` contains metadata proving it was originally read from a FreeCAD file and has not undergone semantic changes, the adapter performs an `exact_native_roundtrip`. This re-emits the original binary streams and XML to ensure 100% fidelity.
Sources: [src/convert/adapters/freecad/Adapter.py:909-940](src/convert/adapters/freecad/Adapter.py#L909-L940)

### Reconstruction (Rebuild)
If the document was modified or originated from another CAD system (e.g., SOLIDWORKS), the adapter synthesizes a new `Document.xml` and generates the necessary sidecar files.
1. **Manifest Generation**: Converts the document to a JSON manifest embedded in the archive.
2. **XML Synthesis**: Builds an object graph using `PartDesign` and `Part` workbench objects.
3. **Geometry Generation**: Converts neutral B-Rep models into OpenCASCADE `.brp` strings.
Sources: [src/convert/adapters/freecad/Adapter.py:1010-1049](src/convert/adapters/freecad/Adapter.py#L1010-L1049), [src/convert/adapters/freecad/Archive.py:1189-1227](src/convert/adapters/freecad/Archive.py#L1189-L1227)

## Assembly Support

The adapter handles FreeCAD assemblies by mapping `App::Part` and `App::Link` objects to neutral `ComponentDefinition` and `ComponentInstance` records. It supports external references by resolving relative paths within the document root.

### External Document Handling
- **Portability**: If the `portable` option is set, the adapter bundles referenced `.FCStd` files into a subfolder named after the main assembly.
- **Link Mapping**: Re-maps `XLink` attributes in the generated XML to point to the new bundled locations.

Sources: [src/convert/adapters/freecad/Adapter.py:716-787](src/convert/adapters/freecad/Adapter.py#L716-L787), [src/convert/adapters/freecad/Adapter.py:804-839](src/convert/adapters/freecad/Adapter.py#L804-L839)

## Conclusion

The FreeCAD Format Adapter enables high-fidelity CAD interchange by combining direct archive manipulation with a deep understanding of FreeCAD's parametric object model. By partitioning logic between native replay and first-principles reconstruction, it balances the need for lossless round-tripping with the flexibility required for cross-format translation.
Sources: [src/convert/adapters/freecad/Adapter.py:1082-1111](src/convert/adapters/freecad/Adapter.py#L1082-L1111), [re/Methodology.md:32-45](re/Methodology.md#L32-L45)
