# SOLIDWORKS configuration directory records

The internal `ReadMgrHeader` and `WriteMgrHeader` operations read and
construct the version-19000 `Contents/CMgrHdr2` stream. They use a
fresh object map and the shared scalar, text, object and counted-row
handlers. The embedded configuration list contributes a count and
its rows to the manager body.

The codec checks the manager and configuration header roles before
reading their fields. It refuses null rows and references to the
manager. A reference to a mapped configuration header retains that
object's identity. The writer takes a typed directory graph with
explicit field values.

The [authored-row case](../../../../tests/Convert/Solidworks/CmgrHeader/ManagerRowTests.py)
checks independent wire bytes. The
[extended count case](../../../../tests/Convert/Solidworks/CmgrHeader/ManagerCountTests.py)
checks two distinct children and a 65,535-row directory. The
[role cases](../../../../tests/Convert/Solidworks/CmgrHeader/ManagerRoleTests.py)
check refusal and the
[disclosed replay cases](../../../../tests/Convert/Solidworks/CmgrHeader/ManagerNativeTests.py)
check full re-emission of two inputs. Execution awaits remote CI.
Projection from a full configuration manager and native document
construction have separate acceptance requirements.
[Scope and proof](../../../../re/solidworks/records/ManagerDirectorySlice2026.md)
