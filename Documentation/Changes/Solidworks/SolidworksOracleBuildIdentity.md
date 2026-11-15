# Exact executable identity for native inspection

Clean part inspection and retained native tracing now record the actual COM server process and executable identity.
The identity includes the executable name, PE architecture, byte count, SHA-256, and four numeric file-version words.
The required file version is `34.5.2.0604` for SOLIDWORKS 2026 SP05.2.
An executable version mismatch stops inspection before the candidate opens.

The research helper uses the COM server's process identifier to locate its loaded executable.
It reads that executable's version resource without copying vendor software into the repository.
The [process API](https://help.solidworks.com/2026/english/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.ISldWorks~GetProcessID.html),
[module lookup](https://mhammond.github.io/pywin32/win32process__GetModuleFileNameEx_meth.html), and
[version-resource API](https://mhammond.github.io/pywin32/win32api__GetFileVersionInfo_meth.html) describe the identity sources.

Use the existing `InspectFresh.py` and `PrepareSolidworks.py` entry points through the authorized Parallels current-user route.
The identity is recorded in each clean result and in the retained tracing preparation result.
Clean inspection also records the job and inspector hashes, plus supplied generator provenance.
Run `OracleIdentity.py` to inspect an already running COM session without opening, rebuilding, saving, or closing documents.
It does not establish native file acceptance.
Static syntax inspection passed. Native execution evidence is pending.
No local repository tests were run.
