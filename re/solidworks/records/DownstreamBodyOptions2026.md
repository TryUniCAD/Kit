# Downstream body options ownership, SOLIDWORKS 2026

The original image derives a fresh loader value of **zero** for the options DWORD. The complete ordinary application's post-startup value remains unmeasured and unqualified. This checkpoint does not enable `f90`, change a preference, or establish native cache acceptance.

Task `B04-SW2026-DOWNSTREAM-BODY-OPTIONS`, owner `configuration_header`, delivery PR #121. Root owns shared integration and the native oracle. The exit condition is source-bound initialization, setter and consumer ownership with the runtime policy boundary explicit. [Numeric ledger](DownstreamBodyOptions2026.json) · [Source verification](../measurements/2026/DownstreamBodyOptionsSource01.json) · [Prior body construction](DownstreamBodyRepresentative2026.md)

## Exact original and loader value

All addresses below belong to original `sldmodu.dll`, preferred base `0x4b140000`, SHA256 `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`. The word is VA `0x4db5681c`, RVA `0x2a1681c`, width four bytes.

Its `.data` section begins at VA `0x4dabb000`, has virtual size 976,776 bytes, raw file offset 43,486,720 and raw size 595,968 bytes. The word begins at section offset 636,956: 40,988 bytes beyond the raw extent. There is no file-backed DWORD to extract. The [documented PE section rule](https://learn.microsoft.com/en-us/windows/win32/debug/pe-format#section-table-section-headers) fills the virtual remainder with zeros. Thus the fresh loader value is `0`, and bit `0x10` starts clear. This is a format-derived initial value, not an observation of a running SOLIDWORKS process or proof that later initialization cannot change it.

## One whole-word setter

The exact export `moDownstreamIdData_c::s_setDownstreamIdOptions(unsigned int)` is ordinal 38324, entry `0x4b53a0c0`, complete seven-byte leaf ending at `0x4b53a0c7`, original interval SHA256 `abdacd174a91af8d9b5f0cc0d436a4774d25029cc7d3ffe2857aff2958d45efb`.

It assigns the supplied ECX DWORD directly to `0x4db5681c`. It replaces the whole word; it does not OR a flag, normalize to Boolean, look up a preference, or choose an application mode. No call to this setter was executed or observed.

## Neighboring initialization has different owners

The original DLL entry at `0x4cba0c14` reaches the CRT reason router and process-attach path. The C++ initialization table passed to `_initterm` is `[0x4cd3e4d0,0x4cd8c408)`. These four selected original slots lie inside it:

| Slot | Callback | Destination | Source |
| --- | --- | --- | --- |
| `0x4cd47130` | `0x4b164cd0` | DWORD `0x4db56810` | `ut_IsDefinedInDumpOpts(L"_ENABLE_DOWNSTREAM_IDS")` |
| `0x4cd47138` | `0x4b164cb0` | DWORD `0x4db56814` | `ut_IsDefinedInDumpOpts(L"_ENABLE_DOWNSTREAM_IDS_FOR_LIGHTWEIGHT")` |
| `0x4cd47140` | `0x4b164cf0` | DWORD `0x4db56818` | `ut_IsDefinedInDumpOpts(L"_ENABLE_DOWNSTREAM_IDS_OUTPUT_TIMINGS")` |
| `0x4cd47148` | `0x4b164d10` | Container starting at `0x4db56820` | Fresh container initialization |

The three option callbacks each store four bytes. None overlaps `0x4db5681c`. The container's lowest written address is `0x4db56820`; its later float assignment also targets that address. A raw displacement candidate appeared to target `0x4db5681c` only when its four trailing immediate bytes were ignored. Instruction alignment refutes that candidate.

The existing [enable predicate](DownstreamConstructorEnable2026.md) and [application enable receiver](DownstreamDateAndEnable2026.md) are independent of this options word. Neither a nonzero application enable field nor `_ENABLE_DOWNSTREAM_IDS` establishes bit `0x10`.

## Consumers and bounded caller search

The reviewed original instruction references are six reads and one write. Fresh `0x4b5265b6` and update `0x4b53aa2c` use bit `1` for data `be0`. The separate tests at `0x4b539454` and `0x4b539d2e` also use bit `1`. Fresh body construction at `0x4b526648` and update at `0x4b53aadc` require bit `0x10`. The setter is the only aligned write found by the stated search.

The local pinned inventory contains 31 DLL/EXE originals. Normal and delayed import tables were parsed without error and checked against the exact export name and ordinal 38324. There were zero matches. Searches for the decorated and short names in ASCII and UTF-16 found only the model export vocabulary. In the model's first executable section, every byte-position signed rel32 displacement was checked with 0, 1, 2, 4 and 8 following bytes; none targeted the setter. No raw eight-byte setter pointer was found in the model. The wider word-neighborhood scan was reviewed against complete original owners to eliminate misaligned and wrong-immediate-length candidates.

Target-free REA independently provided complete managed/native boundary metadata for the pinned `sldcoreu.dll` and `doccplu.dll`: 1,206 P/Invoke rows and 1,273 native-implementation rows in total, with zero exact setter-name matches. Evidence IDs and canonical private-record hashes are retained in the numeric ledger. No native analysis target or Hopper document was opened.

These are bounded negative searches. The 31 images are not a complete installed-module inventory. Dynamic export resolution, callers in other installed modules and indirect mutation remain unexcluded. There is no source-bound application-mode or preference identifier for selecting bit `0x10` in this checkpoint. A claim that every ordinary runtime necessarily retains zero would exceed the evidence.

## Verification and next discriminating observation

The [source verifier](../../tooling/sw2026/downstream/VerifyBodyOptionSources.py) checks 14 complete function owners, 29 original intervals, four initializer slots, three vocabulary entries, two imports, the setter export/ordinal, the zero-fill geometry, and all 31 caller-image identities/import inventories. Its result is byte-bound in the accompanying source receipt. It never loads a vendor module or reads a CAD input.

The smallest remaining observation is a read-only four-byte sample at the actual loaded model base plus RVA `0x2a1681c` in root's exact, already-owned normal COM oracle. Bind the module hash and loaded identity, then observe after startup, after an ordinary child open/rebuild and immediately before save. Do not call the setter or change preferences. A measured value applies to those contexts; it would not establish every application mode.

No SDK product process, native run, VM call, held-out or other CAD read, shared source edit, option/license change or persistent analysis target occurred. The prior body packet remains unchanged. The whole-runtime policy is `not found`; source-only construction rules remain `partial` until exercised. [CAD criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md) · [Loader phase](../../Playbook/LoaderAnalysis.md) · [Evidence rules](../../Playbook/Evidence.md)
