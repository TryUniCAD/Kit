# MFC runtime-view inspection

The research tool [InspectMfcRuntime.py](../../../../re/tooling/sw2026/InspectMfcRuntime.py) inspects the effective mapped view of the exact System32 Microsoft MFC runtime inside its own x64 Python analysis process. It resolves ordinals `12087` and `14278` without invoking either address or any `CArchive` method. The purpose is to supply bounded evidence for the still-provisional `su_CMapStringToInt` count dependency in the [common-owner record](../../../../re/solidworks/records/CommonPartOwners2026.md).

This is an explicitly authorized extension from filesystem inspection to loading a generic Microsoft runtime into an owned analysis process. Ordinary OS DLL initialization and finalization can run during the load and release. The tool does not load SOLIDWORKS modules, use CAD or COM, attach to another process, inject code, enumerate existing applications, or operate services or licensing. Production conversion acquires no runtime dependency from this research tool.

## Input identity and invocation

The oracle owner reviews, commits and executes the tool in a new guest x64 Python process. The implementation worker must not execute it or access the VM. Stage this script together with the unchanged committed [InspectMfcFiles.py](../../../../re/tooling/sw2026/InspectMfcFiles.py) helper in the same trusted tool directory. The probe hashes that helper and requires SHA-256 `195a0d90fe26169b31e87234910af29b2b1f5289b58d29a2e91cafca62602960` before using its read-only PE/file inspector. Bytecode-cache writing is disabled.

Supply the retained `MfcDiscovery02/Inventory.json`, SHA-256 `67d0e37be1e2cabdf2e233c66d2654b3caa2dc1692ef285df76190b6eb0b0a87`, authored under source revision `401a1ce515ae58661fa2806891a532b5e0c927c9`. That inventory is used only for identity. The probe performs no filesystem search and does not reopen the SOLIDWORKS executable or any CAD input. Its raw runtime reads are restricted to `mfc140u.dll` in the OS-reported System32 directory; it also records its own Python executable and independently authored tool/helper provenance.

The retained System32 identity is 12,118,600 bytes, raw PE machine `0xaa64`, version words `[14, 50, 35719, 0]`, SHA-256 `88beebf73667ab0d603355f54562aa9cf9316f4d585a40ec93430c6715ffc8d1`. Hash, size, machine and all decoded version-resource entries must agree. That is a raw file identity, not a claim about the effective loaded instruction set.

The following command is an invocation template with placeholder paths and revision, not an execution result:

```powershell
C:\Path\To\x64Python\python.exe -B C:\Research\Tools\InspectMfcRuntime.py --inventory C:\Research\MfcDiscovery02\Inventory.json --output C:\Research\MfcRuntimeView01 --source-revision 0123456789abcdef0123456789abcdef01234567
```

`--output` must name a fresh external task-owned directory whose parent exists. Reparse/symlink paths and paths within repository checkouts are rejected. `--source-revision` records a required operator-supplied full lowercase commit identity; the tool does not run Git to verify it. The parent-owned macOS transport remains a separate receipt.

## Process, loader and export boundaries

The probe requires 64-bit pointers, a raw AMD64 Python executable, and `IsWow64Process2` observations identifying its own emulated AMD64 process on native ARM64. The API's process and native machine values are recorded separately, without using the environment's architecture strings as proof. See Microsoft's [IsWow64Process2 contract](https://learn.microsoft.com/en-us/windows/win32/api/wow64apiset/nf-wow64apiset-iswow64process2).

It rejects a process that already contains `mfc140u.dll`. It then calls `LoadLibraryExW` with the full OS-reported System32 runtime path and flags `LOAD_LIBRARY_SEARCH_DLL_LOAD_DIR | LOAD_LIBRARY_SEARCH_SYSTEM32` (`0x900`). Dependency resolution is therefore restricted to that DLL directory and System32; no process-wide DLL search settings change. This is a normal executable mapping, because a data-file mapping does not supply normal exported function resolution. See [LoadLibraryExW](https://learn.microsoft.com/en-us/windows/win32/api/libloaderapi/nf-libloaderapi-loadlibraryexw) and [DLL search order](https://learn.microsoft.com/en-us/windows/win32/dlls/dynamic-link-library-search-order).

The returned module path must identify the same file. `K32GetModuleInformation` supplies the mapped base and image bounds using only the current-process pseudo-handle. PE headers and selected directory data are read with `ReadProcessMemory` on that same handle, with per-read and module bounds checked. No `OpenProcess` call or foreign process handle exists in the tool. The relevant Microsoft contracts are [module information](https://learn.microsoft.com/en-us/windows/win32/api/psapi/nf-psapi-getmoduleinformation) and [ReadProcessMemory](https://learn.microsoft.com/en-us/windows/win32/api/memoryapi/nf-memoryapi-readprocessmemory).

For each requested ordinal, the tool checks the effective export table for an assigned, nonforwarded address in an executable section. It calls `GetProcAddress` using the documented low-word ordinal representation, records the returned pointer and compares it with the mapped export-address-table entry. A nonzero pointer alone is insufficient: the [GetProcAddress documentation](https://learn.microsoft.com/en-us/windows/win32/api/libloaderapi/nf-libloaderapi-getprocaddress) explicitly permits invalid nonzero addresses for holes in some ordinal tables.

Microsoft documents that the OS can transform an [ARM64X image](https://learn.microsoft.com/en-us/windows/arm/arm64x-pe) into different architecture views at load time, while the raw image defaults to an ARM64 presentation. This probe therefore keeps raw file metadata, actual process architecture, effective mapped PE headers and OS-resolved export addresses separate. An AMD64-facing mapped PE header does not, by itself, prove that every captured instruction is x64 rather than a thunk or ARM64EC code. The probe never disassembles or calls a captured address and never infers a count rule from a machine identifier.

An effective machine other than AMD64, missing/forwarded/nonexecutable exports, a resolver/table disagreement, a target outside the selected module, inaccessible ranges, changed raw identity or failed cleanup produces a nonzero exit and a failed report. When both addresses remain within the selected module but disagree with the export table, both bounded windows can be captured for diagnosis, while admission still fails. There is no architecture or ordinal fallback.

## Private outputs

Progressive `Inventory.json` checkpoints precede the loader, effective-export reads, each ordinal resolution and owned-handle release. The terminal report records Python/tool/source identities, its own PID, raw file identity before/after, mapped architecture and sections, both export identities, all private-range lengths/hashes and release status. It preserves partial evidence on a caught failure. The runtime file's hash, size, modification time and integer file identity must remain unchanged across inspection.

The only binary outputs are bounded private range captures beneath the fresh external directory:

| Capture | Maximum bytes | Meaning |
| --- | ---: | --- |
| Mapped headers | 65,536 | Effective header bytes, not raw file-offset reconstruction |
| Effective export directory | 1,048,576 | The selected mapped directory, including its table framing |
| Exception directory | 2,097,152 | Raw directory bytes, with no presumed AMD64 unwind layout |
| Load-configuration directory | 16,384 | Raw architecture/loader metadata, without following internal pointers |
| Each ordinal entry/resolved window | 4,096 | Bounded executable-section window, possibly a thunk or partial function |

Total captured bytes cannot exceed 4 MiB. Each file ends in `.private.bin`; its report entry gives the mapped address, RVA, size and SHA-256. Every range sets `full_function_extent_claimed` to false. The probe does not claim that a fixed window contains a complete function, that one exception row represents every chained fragment, or that a hybrid exception directory has a 12-byte AMD64 record shape. The [unwind-boundary gotcha](../../../Gotchas/Conversion/Solidworks/Inspection/ExceptionDirectoryBoundsUnwindRecords.md) remains applicable.

These outputs contain proprietary runtime bytes and are never commit or publication inputs. Keep the entire raw output outside checkouts under the [research artifact policy](../../../Reference/Research/ResearchArtifacts.md). Public findings can record reviewed identities, addresses, independently derived rules and appropriately redacted metadata; they cannot reproduce the captured code or private paths.

The `finally` path releases only the module reference this analysis process acquired. Even if a checkpoint write fails, release is still attempted. It never closes an application or releases another process's module reference. Process exit ends only this owned Python analysis process.

## Results and verification limits

Exit `0` and `mapped_abi_view_verified=true` mean the bounded current-process inspection, identity checks, effective AMD64-facing export checks and own-reference release completed. They do not prove either count implementation, its instruction set, archive grammar or native CAD behavior. `instruction_set_proven`, `native_implementation_bound` and `acceptance` remain false on every path. Matching counts require a separate review of the actual reached bodies, complete extents and relevant loader/store branches before `su_CMapStringToInt` can be promoted.

This draft received AST and static source/link review only. The worker did not run the probe, import its modules, execute a schema or codec, read CAD/held-out payloads, run tests, access the guest or operate licensing. Runtime-view capture and new count facts are pending with the oracle owner. The [filesystem-discovery entry](SolidworksMfcFileDiscovery.md) remains separate from this newly authorized loading scope.

> YOU DO NOT HAVE THE ORACLE. DO NOT LAUNCH, ATTACH TO, OR AUTOMATE THE CAD APPLICATION. REQUEST MEASUREMENTS FROM THE ORACLE OWNER.

The repository [standard PR skill](../../../../.agents/skills/standard-pr-practice/SKILL.md), [CAD criteria](../../../Reference/Operations/CadSuccessCriteria.md), complete [instruction book](../../../../re/Playbook/README.md) and [loader chapter](../../../../re/Playbook/LoaderAnalysis.md) remain authoritative. The criteria state:

> The first is success under every criterion on this page.
> The second is the end of the available context.
> Missing grammar is the work. It is not a blocker.

The [hybrid-export gotcha](../../../Gotchas/Conversion/Solidworks/Inspection/HybridPeExportsDependOnProcessArchitecture.md)
records why raw ordinal lookup does not bind the emulated application's count implementation.
The full writer goal, the string-map count boundary and the separate radial callback boundary remain unresolved by this tool.
