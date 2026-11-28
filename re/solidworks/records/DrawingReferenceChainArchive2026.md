# Drawing reference-chain archive admission

Complete original drawing stream parity and writer acceptance remain false. Both disclosed originals now complete the component-profile subtree, including all three chain/list bodies, before rejecting the later root reference-map owner `moEdgeRef_c` schema 1.

Task: **B04-SW2026-DRAWPROPS / ordinary drawing reference chains**. Owner: `/root/flag_ownership`; root owns integration and the native oracle. Delivery: PR #121. Dependencies are the [component-profile reader](DrawingComponentProfileArchive2026.md), the already published [native reference-chain proof](PlanarMateReferenceChains2026.md), and the shared SDK reference fields. This slice changes one concrete-class admission table. It adds no field grammar, constructor, source values or writer capability.

## Reused grammar and concrete identity

The actual layouts already flow from [ReferenceFields](../../../src/convert/adapters/solidworks/Archive/Bodies/Layouts/ReferenceFields.py) through Config and Resolved into the drawing layout. [FrontSchemas](../../../src/convert/adapters/solidworks/Drawing/Definition/Linked/FrontSchemas.py) previously excluded three concrete classes. The new table admits only native schema one for `moChainComponent_c`, `moReferenceChain_c` and `moExtFeatureList_c`.

The [independent current-build proof](DrawingReferenceChainArchive2026.json) rechecks the original SOLIDWORKS `34.5.2.0604` image, SHA-256 `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`, preferred base `0x4b140000`. Actual primary-table slots and runtime getters bind all three concrete versioned schema words to `0x80000001`. The inherited `moComponent_c` descriptor instead has schema `0xffff`; it is reused as a field base and is not newly admitted as a concrete schema-one object. The existing [abstract-base gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Assembly/AssemblyConcreteComponents.md) remains applicable.

| Owner                | Complete native serializer                                                                                                             | Existing ordinary-19000 body                                                                             |
| -------------------- | -------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| `moChainComponent_c` | `[0x4c21b8c0,0x4c21bfac)`, SHA-256 `2168c75b8e3f00d0bc3200969a5e1af384d0aa48040c052725256fd6587758eb`                                  | Base component `owner` object; `f20` chain object; `f30:u32`                                             |
| `moComponent_c` base | `[0x4c21cac0,0x4c21d271)`, SHA-256 `1c0667b25d0693208ffa6e93843aba8a10984c12fd259f51644ba70e140d9f4c`                                  | One owner object tag in the ordinary non-database archive                                                |
| `moReferenceChain_c` | Seven chained fragments spanning `[0x4b66e370,0x4b66e98f)`, SHA-256 `eb0860ef9ac860fa2084f8e04210d68caf347b146c3d6085cbbe26e6e4ce68a9` | `f24:u16`; conditional `has_f18:i32`; `f08` feature-list object; `f20:i32`; embedded configuration `f40` |
| `moExtFeatureList_c` | `[0x4c1784f0,0x4c178a22)`, SHA-256 `2d846240cb81af7be17ad3858f88954ae91b955161a03eefa31c81c92774b358`                                  | Signed `i32 n` wire word interpreted as an unsigned low-32-bit iteration count, then ordered object rows |

The embedded configuration uses the unchanged CString and signed-id fields. Its exact `sldarchiveu.dll` serializer is independently rehashed in the JSON. Count safety limits remain unchanged. The SDK does not substitute source list lengths, stamps, acquisition counts, paths, modes or configuration values.

## Drawing context and raw-state boundary

The selected named drawing has outer conditions zero and temporarily sets `0x40` inside the common model-view body. The complete native component, chain-component and reference-chain functions contain 27 `moArchiveHelper_c::hasCondition` calls. Their masks all give the same zero result for conditions zero and `0x40`; the list serializer has no such condition calls. The two register-forwarded mask-one arguments are independently bound to the nonvolatile `ESI=1` assignment rather than left as guessed immediates.

The optional reference-chain owner word tests mask `0x80000001`, so it is absent in both selected modes. The inherited legacy component-name branch before `0x144`, pre-`0x837` stamp handling, older chain/configuration/list layouts and database archive paths remain outside this ordinary-19000 route. The existing framing, concrete-schema checks, component-profile context guard and unsupported-dependency diagnostics remain in force.

Native load can resolve owners and canonicalize chains through runtime manager state. This raw codec retains the serialized owners, aliases and scalar words. It does not replay native runtime fixups or infer semantic constructor defaults. The shared class/object counter and map ownership are unchanged.

## Exact source observation and remaining dependency

The [sanitized reader receipt](../measurements/2026/DrawingReferenceChainReader01.json) binds the source closure and actual two original drawings. A private SDK decoder observation records complete returns for `moCompProfile_c`, `moChainComponent_c`, `moReferenceChain_c` and `moExtFeatureList_c` in both originals at effective conditions `0x40`. This is SDK decoder state, not a native runtime trace or full source-store comparison.

The next rejection is later at drawing `model.f1570.rows.ref`: concrete `moEdgeRef_c` schema one, effective conditions zero and `ctx87c=0`. The whole Definition remains incomplete. No re-emission of either original stream is counted as passed. Root independently replayed the exact frozen chain candidate through all 43 prior-profile workers: 18 workers for six disclosed independent pairs and 25 expected rejections. All passed with the source immutable. Its existing generated profiles do not establish full original source admission, and this replay does not claim a store of either still-unsupported original. AST, Black, Ruff, strict Mypy, strict Pyright and steering pass on the changed SDK file. The worker executed no test suite or native application.

The original writer manifest `645a423b76792abc04823cdf44a72c3df940847d1e4bd966dc07e6b57ea3d864`, original source-family rejection and partial-geometry verdict remain fixed. This tranche changes no public adapter entry point or construction rule. It imports no research runtime and adds no captured data, recorded field program or fallback.

> The first is success under every criterion on this page.
> The second is the end of the available context.

The complete CAD goal remains unfinished; the next raw grammar owner is the root edge-reference map.
