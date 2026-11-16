# WOW64 unknown can accompany an AMD64 process

## Expectation

The `IsWow64Process2` process-machine output always identifies the actual architecture of an emulated x64 process on ARM64. Requiring that output to equal `0x8664` is sufficient process admission.

## Actual behavior

The committed `MfcRuntimeView01` probe under source revision `45c0b91e773902258b5f4ce8218e7d276fbc5628` stopped at that guard with transport exit `1`. Its owned PID was `9068`. The guest report recorded:

| Observation | Value |
| --- | --- |
| `IsWow64Process2` process machine | `0`, `IMAGE_FILE_MACHINE_UNKNOWN` |
| Native machine | `0xaa64`, ARM64 |
| Pointer width | 8 bytes |
| Python raw executable machine | `0x8664`, AMD64 |
| Python executable SHA-256 | `ca60cf785b2314a6d6599eced15bdf094e6db171bec996b97a70b995942c3c37` |
| Python version presentation | Python 3.12.7, 64-bit AMD64 |
| Probe source SHA-256 | `69f60b00f2942d236a01edd1da52bc8276e48813508783c86a20fe94e111b3df` |

The guest `Inventory.json` SHA-256 is `f3c7169091cc0a91693577a61fc8114af46347ca39747e9b2e593e8937de4600`. The sibling `MfcRuntimeView01.Host.json` receipt has SHA-256 `42e6d734178ebd9dcbcdc985d65c36c1a056e843e15cd92b8ce93a68b5c0042e` and confirms transport exit `1`. Both remain private and immutable. The tool stopped before its MFC load call; it produced zero private ranges and no ordinal or mapped-MFC observations. This does not inventory every module that might already have existed in the Python process.

The contradiction is between the guard's interpretation and the measured API/header observations. It does not establish an operating-system defect. Microsoft's [`IsWow64Process2` contract](https://learn.microsoft.com/en-us/windows/win32/api/wow64apiset/nf-wow64apiset-iswow64process2) permits an unknown process-machine result when the process is not classified as WOW64. Unknown is not the ARM64 machine identifier and must not be replaced with the native-host value.

The [`MACHINE_ATTRIBUTES` documentation](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/ne-processthreadsapi-machine_attributes) expressly distinguishes x64-on-ARM64 operation in the OS root namespace from a WOW64 namespace container. That documented distinction explains why the old universal WOW64-classifier assumption was unsuitable. It does not substitute for measuring this process through the dedicated architecture query.

## Workaround

Query `GetProcessInformation(ProcessMachineTypeInfo)` and require its documented actual-process machine field to be AMD64. Also require eight-byte pointers, an AMD64 raw executable, an AMD64 mapped main-image header matching that same file, valid mapped image bounds, and a native ARM64 host. Preserve the WOW64 result separately: accept zero only with that full independent evidence, and reject conflicting nonzero values. Missing or unsupported evidence fails before MFC loading.

The additional query uses only the current-process handle. No external process, CAD application, COM interface, service, registry or licensing state is inspected. The [process-architecture change](../../../../Changes/Solidworks/Model/SolidworksMfcProcessArchitectureAdmission.md) gives the exact result structure, query-class identity and source links. The [runtime-view entry](../../../../Changes/Solidworks/Model/SolidworksMfcRuntimeViewInspection.md) retains its hybrid-module and ordinal checks.

The amended query has not yet run in the guest. A new committed source identity and unused output directory are the causal inputs for the next probe; repeating the unchanged failed guard is not new evidence. A successful process admission would still leave MFC instruction-set classification, complete count-method bodies and the string-map schema provisional until independently established. Native CAD acceptance is not measured by this probe.
