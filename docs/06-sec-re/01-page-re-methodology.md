<!--
SPDX-License-Identifier: MIT
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt
-->

---
title: "Reverse Engineering Methodology"
wiki_page_id: "page-re-methodology"
---

<details>
<summary>Relevant source files</summary>

The following files were used as context for generating this wiki page:

- [re/Methodology.md](re/Methodology.md)
- [re/README.md](re/README.md)
- [re/solidworks/archive/Grammar.md](re/solidworks/archive/Grammar.md)
- [re/solidworks/features/Revolve.md](re/solidworks/features/Revolve.md)
- [re/tooling/windbg/Multitrace.py](re/tooling/windbg/Multitrace.py)
- [re/tooling/harness/Serialize.py](re/tooling/harness/Serialize.py)
</details>

# Reverse Engineering Methodology

Reverse Engineering Methodology provides a reusable playbook for cracking proprietary binary CAD formats. This framework enables developers to achieve bidirectional interoperability with closed vendor applications like SOLIDWORKS, AutoCAD, CATIA, and NX. The core strategy avoids byte-staring in favor of building a measurement oracle and attacking the format through differential analysis, runtime tracing, and static decompilation.

The methodology ensures that every inference is verified quantitatively against the vendor application itself. By following a structured phase order, the project reduces the complexity of analyzing thousands of serializable classes, focusing only on those that impact geometry and feature history.

## 1. Execution Phases

The reverse engineering process follows a specific order where each phase provides ground truth for the next. This structure manages costs and increases the technical generality of the findings.

| Phase | Description | Key Outcome |
| :--- | :--- | :--- |
| **1. Container Framing** | Analyze the file envelope and enumerate streams. | Identifies standard containers (e.g., ZIP, OLE/CFBF) and magic numbers. |
| **2. Measurement Oracle** | Build an unattended verification loop using the vendor API. | Provides quantitative correctness verdicts (e.g., volume, center of mass). |
| **3. Authored Corpus** | Generate families of documents differing by a single property. | Locates fields for every variable property in the application. |
| **4. Runtime Tracing** | Trace the vendor's reader under a debugger (e.g., WinDbg/cdb). | Recovers object boundaries and index arithmetic. |
| **5. Static Decompilation** | Use Ghidra to analyze the vendor's serialization code. | Identifies authoritative field orders, types, and version gates. |
| **6. Write Path** | Implement the actual product-level converter. | Delivers a verified translator independent of vendor APIs. |

Sources: [re/Methodology.md:38-51](re/Methodology.md#L38-L51), [re/README.md:120-128](re/README.md#L120-L128)

## 2. Quantitative Measurement Oracle

The oracle is the most critical component of the methodology. It uses the vendor's own API (e.g., SOLIDWORKS COM, NXOpen, Pro/TOOLKIT) to verify if a generated or patched file is correct.

*  **Quantitative Verification:** The system measures solid volume and center of mass rather than simple "boolean" opens. It aims for relative matches of $\le 6e-16$.
*  **Process Isolation:** The harness launches one fresh vendor process per candidate to prevent session poisoning from crashes.
*  **Batch Controls:** Known-good files are measured at the start and end of every batch. If a control fails, the entire batch is discarded.
*  **Modal Management:** A watchdog thread clicks through startup modals or inconsistent toolbar dialogs to prevent blocking automation.

Sources: [re/Methodology.md:73-95](re/Methodology.md#L73-L95), [re/tooling/harness/Serialize.py:535-560](re/tooling/harness/Serialize.py#L535-L560)

```mermaid
flowchart TD
    Start[Start Verification Batch] --> Control1[Measure Control File]
    Control1 --> Process[Launch Isolated Vendor Process]
    Process --> Watchdog[Watchdog: Dismiss Modals]
    Watchdog --> Measure[Measure Volume/CoM]
    Measure --> Kill[Kill Process & Helpers]
    Kill --> Next{Next File?}
    Next -- Yes --> Process
    Next -- No --> Control2[Measure Control File]
    Control2 --> Validation{Controls Match?}
    Validation -- Yes --> Success[Accept Batch Results]
    Validation -- No --> Failure[Discard Batch]
```

The diagram represents the automated verification loop used to ensure data integrity during reverse engineering. Sources: [re/Methodology.md:75-103](re/Methodology.md#L75-L103)

## 3. Differential Corpus Analysis

Differential analysis involves authoring documents that vary by exactly one property (e.g., extrude depth, profile type, or end condition). By diffing these files, the methodology identifies the exact byte locations of authored parameters.

*  **Control Pairs:** Authoring the same document twice reveals timestamps and session IDs (the noise floor).
*  **Family Ladders:** Files with increasing feature counts (1, 2, 3... n) expose per-feature record blocks.
*  **Round-Trip Artifacts:** Generated files are tagged to prevent them from being mistaken for vendor-source documents.

Sources: [re/Methodology.md:112-132](re/Methodology.md#L112-L132), [re/solidworks/features/Revolve.md:21-30](re/solidworks/features/Revolve.md#L21-L30)

## 4. Runtime Runtime Trace and Segmentation

Runtime tracing recovers object boundaries, which is essential for structural edits like reordering or deleting features. Many CAD formats use MFC-style `CArchive` serialization, where classes are defined once and subsequent instances are indices into a map.

*  **Entry Point Hooking:** The debugger hooks functions like `swccu!su_CArchive::ReadObject` or `ReadClass`.
*  **State Capture:** The script logs the stream position, map counter, and buffer length at every hit.
*  **Verification by Re-emission:** The trace is successful if reparsing the stream into a symbolic model and re-emitting it yields a byte-identical output.

Sources: [re/Methodology.md:144-166](re/Methodology.md#L144-L166), [re/tooling/windbg/Multitrace.py:84-118](re/tooling/windbg/Multitrace.py#L84-L118)

```mermaid
sequenceDiagram
    participant D as Debugger (cdb)
    participant V as Vendor DLL (swccu.dll)
    participant L as Trace Log
    
    D->>V: Set Breakpoint su_CArchive::ReadObject
    V->>D: Breakpoint Hit
    Note over D: Capture rsp, rcx (this), map_count
    D->>L: Write Stream Position & Map Index
    D->>V: g (Continue execution)
```

The sequence diagram shows the runtime instrumentation of the serialization API to recover object boundaries. Sources: [re/tooling/windbg/Multitrace.py:46-56](re/tooling/windbg/Multitrace.py#L46-L56), [re/Methodology.md:154-162](re/Methodology.md#L154-L162)

## 5. Static Decompilation Strategy

Static analysis via Ghidra provides the authoritative types and logic for fields discovered during differential analysis.

*  **API Renaming:** Decompilation results are improved by renaming overloaded `operator>>` calls to typed functions like `get_double` or `get_i32` based on demangled parameter types.
*  **Vtable Slot Identification:** By mapping RTTI-named vftables to specific serialization slots (e.g., vtable slot 5 for `Serialize`), the methodology creates a class-to-serializer map for thousands of classes.
*  **Version Gating:** Static analysis reveals code branches that only execute for specific document versions, explaining length differences that are invisible to single-version corpus diffing.

Sources: [re/Methodology.md:186-218](re/Methodology.md#L186-L218), [re/README.md:131-135](re/README.md#L131-L135)

## 6. Verification and Attestation Discipline

Engineering discipline is maintained through a three-tier confidence vocabulary applied to every field identified.

| Confidence Level | Definition |
| :--- | :--- |
| **Confirmed** | Field is read in decompilation AND reproduces a real traced span or measured number. |
| **Partial** | Field is read in decompilation, but no corpus file exercises the branch or varies the value. |
| **Not Found** | Field is present in records but its purpose remains unresolved. |

**Key Rule: Stale vs. Wrong Caches.** Redundant caches (e.g., Parasolid body caches or bounding box data) should be left stale or deleted. Writing a "plausible but wrong" cache often results in crashes or silent geometry corruption, whereas vendor applications usually recompute stale caches.

Sources: [re/Methodology.md:231-255](re/Methodology.md#L231-L255), [re/README.md:104-114](re/README.md#L104-L114), [re/solidworks/archive/Grammar.md:225-240](re/solidworks/archive/Grammar.md#L225-L240)

## Summary

The Reverse Engineering Methodology prioritizes quantitative measurement over byte-level guesswork. By utilizing a "Measurement Oracle" as the ultimate source of truth, and coordinating subagents through file-based ownership, the project successfully cracks complex formats like SOLIDWORKS 2025. The transferable assets are the tools found in `re/tooling/`, which provide a standardized way to analyze containers, trace runtimes, and decompile serialization logic across any proprietary CAD format.

Sources: [re/Methodology.md:310-335](re/Methodology.md#L310-L335), [re/README.md:155-163](re/README.md#L155-L163)
