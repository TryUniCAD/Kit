<!--
SPDX-License-Identifier: MIT
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt
-->

---
title: "CATIA Format Adapter"
wiki_page_id: "page-adapter-catia"
---

<details>
<summary>Relevant source files</summary>

The following files were used as context for generating this wiki page:

- [src/convert/adapters/catia/Adapter.py](src/convert/adapters/catia/Adapter.py)
- [src/convert/adapters/catia/Container.py](src/convert/adapters/catia/Container.py)
- [tests/convert/catia/CatiaTests.py](tests/convert/catia/CatiaTests.py)
- [re/Methodology.md](re/Methodology.md)
- [src/convert/adapters/catia/Format.py](src/convert/adapters/catia/Format.py)
</details>

# CATIA Format Adapter

The CATIA Format Adapter enables the Kit SDK to read and write CATIA V5 files. It handles the extraction of geometry, feature history, and assembly structures from `.CATPart` and `.CATProduct` containers. The adapter treats these files as CFBF (Compound File Binary Format) envelopes containing various binary streams and records.

Sources: [src/convert/adapters/catia/Adapter.py:46-75](src/convert/adapters/catia/Adapter.py#L46-L75), [re/Methodology.md:280-284](re/Methodology.md#L280-L284)

## Architecture Overview

The adapter consists of four primary components that implement the standard Kit adapter interface. These components handle metadata identification, source probing, document reading, and destination writing.

```mermaid
classDiagram
    class CatiaAdapter {
        +probe(Source) ProbeResult
        +read(Source, ReadOptions) CadDocument
        +write(CadDocument, Destination, WriteOptions) WriteResult
        +supports(CadDocument, Destination) bool
    }
    class CatiaMetadata {
        +info AdapterInfo
    }
    class CatiaReader {
        +read(Source, ReadOptions)
    }
    class CatiaWriter {
        +write(Doc, Target, Options)
    }
    class CatiaSupport {
        +CanSupport(Doc, Target)
    }
    CatiaAdapter --|> CatiaMetadata
    CatiaAdapter --|> CatiaReader
    CatiaAdapter --|> CatiaWriter
    CatiaAdapter --|> CatiaSupport
```

The diagram shows the class hierarchy of the CATIA adapter, combining metadata, reading, writing, and support logic.
Sources: [src/convert/adapters/catia/Adapter.py:151-240](src/convert/adapters/catia/Adapter.py#L151-L240)

## Container Structure

CATIA V5 files utilize the `V5_CFV2` container format. This format organizes data into an outer directory and optional nested directories, each containing multiple data streams. The adapter parses these streams to identify the document type and extract payloads.

### Supported Streams
| Stream Name | Purpose | Role |
| --- | --- | --- |
| `1000_00000002_2` | Primary Part Data | Feature History |
| `1000_00000001_1` | Primary Product Data | Assembly Structure |
| `Format` | Document Type Marker | Metadata |
| `KitInterchange` | Embedded Kit Manifest | Document |
| `CATSummaryInformation` | Version and Application Info | Metadata |

Sources: [src/convert/adapters/catia/Adapter.py:80-95](src/convert/adapters/catia/Adapter.py#L80-L95), [src/convert/adapters/catia/Adapter.py:417-434](src/convert/adapters/catia/Adapter.py#L417-L434)

## Read Logic

The `CatiaReader` processes `V5_CFV2` archives by detecting the document type and extracting native payloads. If a `KitInterchange` stream exists, it restores the neutral document from the embedded manifest.

```mermaid
flowchart TD
    A[Start Read] --> B{Manifest Present?}
    B -- Yes --> C[Read Embedded Document]
    B -- No --> D[Detect Document Type]
    D --> E[Identify OSMX Graphs]
    E --> F[Extract Brep/Tessellation]
    F --> G[Build CadDocument]
    C --> H[Apply Read Filters]
    H --> G
```

The flow diagram illustrates the decision path between reading a native CATIA file and restoring an embedded Kit document.
Sources: [src/convert/adapters/catia/Adapter.py:165-220](src/convert/adapters/catia/Adapter.py#L165-L220), [tests/convert/catia/CatiaTests.py:277-290](tests/convert/catia/CatiaTests.py#L277-L290)

### Payload Identification
The adapter classifies binary streams based on signatures and declarations:
*  **OSMX**: Native feature history or assembly structure.
*  **CGM**: Native B-Rep geometry.
*  **MFBRP**: B-Rep topology data.
*  **CGR**: Native tessellation (SceneGraph/SurfacicReps).

Sources: [src/convert/adapters/catia/Adapter.py:734-790](src/convert/adapters/catia/Adapter.py#L734-L790)

## Write Logic

The `CatiaWriter` supports three primary write modes based on the availability of a "donor" document and the target configuration.

### Write Modes
| Mode | Description | Compatibility |
| --- | --- | --- |
| `exact_native_roundtrip` | Replays original native bytes for unmodified documents. | `native-exact` |
| `native_base_with_neutral_edits` | Preserves native streams but adds a neutral manifest for edits. | `native-base-neutral-overlay` |
| `generated_cfv2` | Generates a new CFV2 container from scratch with embedded neutral data. | `kit-neutral-only` |

Sources: [src/convert/adapters/catia/Adapter.py:245-360](src/convert/adapters/catia/Adapter.py#L245-L360)

### Native Base Preservation
When `native-base-neutral-overlay` is active, the adapter appends a `KitInterchange` stream to an existing CATIA file. This preserves the original native features for CATIA while allowing Kit to store changes in a neutral format.

```mermaid
sequenceDiagram
    participant W as CatiaWriter
    participant D as Donor Bytes
    participant M as Manifest
    participant T as Target File
    W->>D: Load Native Base
    W->>M: Pack Neutral Document
    M->>M: Compress (Zlib Level 9)
    W->>D: Append Cfv2 Stream "KitInterchange"
    D->>T: Write Combined Bytes
```

This sequence shows how the adapter overlays neutral Kit data onto native donor bytes.
Sources: [src/convert/adapters/catia/Adapter.py:302-330](src/convert/adapters/catia/Adapter.py#L302-L330), [src/convert/adapters/catia/Adapter.py:488-500](src/convert/adapters/catia/Adapter.py#L488-L500)

## Semantic Validation

To ensure data integrity, the adapter calculates a `catia.roundtrip_sha256` digest. This digest is a hash of the document's semantic content, excluding specific source-dependent metadata and the native envelope payloads themselves.

Sources: [src/convert/adapters/catia/Adapter.py:215-225](src/convert/adapters/catia/Adapter.py#L215-L225), [src/convert/adapters/catia/Adapter.py:1100-1150](src/convert/adapters/catia/Adapter.py#L1100-L1150)

## Implementation Details

The adapter uses standard Python libraries for low-level data handling:
*  `struct`: For parsing binary headers and extent offsets.
*  `hashlib`: For generating SHA256 digests of streams and manifests.
*  `zlib`: For compressing and decompressing the embedded Kit manifest.

Sources: [src/convert/adapters/catia/Adapter.py:8-40](src/convert/adapters/catia/Adapter.py#L8-L40), [src/convert/adapters/catia/Container.py:10-30](src/convert/adapters/catia/Container.py#L10-L30)

### OSMX Graph Extraction
The adapter identifies native features by searching for `OSMX` markers within the container. It maps these graphs to `FeatureStep` and `Body` records in the `CadDocument`, allowing for basic structural representation of the part history.

Sources: [src/convert/adapters/catia/Adapter.py:640-700](src/convert/adapters/catia/Adapter.py#L640-L700)

### Conclusion
The CATIA Format Adapter provides a robust bridge between CATIA V5 files and the Kit neutral model. By supporting both native byte replay and generated neutral carriers, it ensures maximum interoperability while preserving original proprietary data whenever possible.
