# Recursive ordinary assembly header activity in SOLIDWORKS 2026

The configuration walk expands each ordinary resolved assembly occurrence before copying its activity count to the document header. The new construction evidence closes the recursion and repeated-target rules within the visible, fully resolved, rigid, acyclic profile. This extends the prior activity-handler and UI/header bridge findings. [Existing count lifecycle](AssemblyConstruction2026.md#header-component-activity-count) · [Disclosed typed and native source audit](DisclosedNestedAssemblyArchiveAudit2026.md)

## Pinned code ownership

Addresses for the traversal below use the preferred image base of `sldmodu.dll`, `0x4b140000`. The original binary SHA-256 is `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`. LLVM objdump 21.0.0 independently disassembled the exact original PE ranges. Exception-directory entries identify the following complete native body ranges, with ends exclusive. The digests cover original file-backed bytes.

| Function | Begin | End | SHA-256 |
| --- | --- | --- | --- |
| `moAssemblyWalk_c` constructor | `0x4b6f8300` | `0x4b6f843d` | `dacb99b4543e1ad968dbaad92d1901e4c1478daab7c41b3af1b77a415d9368e4` |
| `moAssemblyWalk_c::_walkR` | `0x4b6fa5a0` | `0x4b6fab5d` | `245bcb859bf7fe4166039f5da04a70e59b9124309bf99fad85d66eb398bb3ea9` |
| `moAssemblyWalk_c::startWalk` | `0x4b6fe0f0` | `0x4b6fe1df` | `b73db05b601102d792711e81fc1b90cb3dcaa3397546ddb275eac234b6529379` |
| `configurationWalker` constructor | `0x4b8c4580` | `0x4b8c4a0c` | `28cf5d1d442d627ac5db6389b10f2bcfdf01f880c5db91a3e3fee72ad56733f7` |
| `configurationWalker::doGoingDown` | `0x4b8cd440` | `0x4b8cdb31` | `00313e936192e3f77f471fd31ebb9c43ce6c4577ec95401c37b95c9d597903f4` |
| Reference activity handler | `0x4b8ce7f0` | `0x4b8cf6fb` | `0a8b3b0574a012e31623fe9e9cd6747247646d737fdb5312a05750e519c80b9a` |
| Full configuration walk driver | `0x4b8d3630` | `0x4b8d3f27` | `f488163423abd3c1a1a5599bc956cb30918705aabb39d68a2632fb05ff0759e4` |
| Ordinary resolved-state activation helper | `0x4b8d6d90` | `0x4b8d898d` | `0d0e9a04c2f0a160283801b452f48e834e9023d9063860560a0b51ff1d55e631` |

The first five function pointers at configuration-walker table `0x4cece728` bind slots `+0`, `+8`, `+0x10`, `+0x18`, `+0x20` to `0x4b8cd440`, `0x4b8cde90`, `0x4b8d5810`, `0x4b6fe0f0`, `0x4b6fa5a0`. The original 80-byte range beginning at that table has SHA-256 `1684c9ca0518947a1df1d512a1bc165047a979cb58e2a1570f5410ca2d68b63e`. These pointers connect the concrete callbacks to the inherited traversal.

## Count each placement path

The configuration-walker constructor passes zero as the base walker's fourth argument at `0x4b8c45d8`. The base constructor writes that argument to member `+0xe8` at `0x4b6f8376`. The optional seen-model test at `0x4b6fa699–0x4b6fa737` requires this member to be nonzero, so that deduplication branch is disabled for the configuration walk.

Before traversing, the full driver calls the `considerTop` setter with one at `0x4b8d3752–0x4b8d375a`, then the `clearDoIf` setter with zero at `0x4b8d375f–0x4b8d3764`. The tiny setters assign members `+0x2c` and `+0x30`. These choices start at the model's self reference and disable the ordinary do-if prefilter. The driver invokes walker slot `+0x18` at `0x4b8d3bb3`. `startWalk` obtains the actual self reference through model slot `+0x16d0` and dispatches walker slot `+0x20` at `0x4b6fe155`.

The recursive walker invokes `doGoingDown` at `0x4b6fa74f`. For a reference, that callback calls the activity handler at `0x4b8cd5d8`. The handler compares the current reference with the containing model's actual self pointer at `0x4b8ce847–0x4b8ce851`. Only that self event resets configuration `f4b0` to zero at `0x4b8ce8b3` and returns before the normal increment. Descending into a target assembly walks its live feature list without introducing another self event.

For an ordinary reference whose final activation status is zero, the handler increments the current configuration's `f4b0` at `0x4b8cf6c7`. The recursive walker checks its callback status, target-is-assembly predicate and resolved model at `0x4b6fa76c–0x4b6fa7af`. It then traverses that target's live `f60` feature list and dispatches the same walker through slot `+0x20` at `0x4b6fa86b` for each child. The root model and current configuration stored in the walker stay the same through this recursion. Repeated placements therefore contribute their own event and each of their descendant paths.

Within the admitted profile the computed activity function is

```text
activity(part) = 0
activity(assembly) = sum(1 + activity(occurrence.target) for each direct occurrence)
```

A document definition can be shared by many occurrences. The count uses the placements. The disclosed SingleFrame and MixedFrame have direct counts 1 and 3, expanded counts 2 and 7, and corresponding saved header counts 2 and 7. The static walk explains those results without using them as construction values. The sources and the corrected native replay remain bound by the [typed audit receipt](../measurements/2026/DisclosedNestedAssemblyArchiveAudit01.json).

## Lifecycle and admitted domain

The header constructor seeds `fc4 = 0`, and the base configuration constructor seeds its activity count at `f4b0 = -1`. A completed walk replaces the configuration seed. Its normal completion loads `f4b0` at `0x4b8d3e72` and calls document context slot `+0x460` at `0x4b8d3e7b`. The pinned context/UI bridge then copies the supplied value into the owning header and UI cache. The save path can copy that cached count to a saved header. A generated graph representing completed ordinary insertion must compute the activity of each containing definition and use that value for its configuration and applicable headers. [Header construction](HeaderConstruction2026.md) · [Context and UI bindings](AssemblyConstruction2026.md#header-component-activity-count)

The full reference handler retains separate suppression, graphics, SpeedPak, virtual, viewer, flexible and partial-open branches. In the normal helper, suppression state zero or nonzero graphics state leads to nonzero status at `0x4b8d6f43–0x4b8d6f53`, and zero-status resolved completion returns through `0x4b8d87fd`. The driver uses a separate shrink-wrap count source when configuration `f784` is nonzero. A generator using the recurrence must admit the fully active, visible, rigid, resolved profile explicitly and reject those additional states until their own event/status semantics are established. The general activity-walk rule remains documented in the earlier record.

This tranche establishes static construction dataflow and corroborates the disclosed saves. It adds zero native runs or generated-output acceptance claims. The REA original-image request encountered an existing foreign Hopper lease. The investigation closed its own metadata target and used the independently hashed original PE plus LLVM disassembly. The evidence retained here consists of rules, addresses and digests. Proprietary listings remain outside the checkout.
