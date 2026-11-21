# The body atom-ID getter can materialize a runtime pointer mirror

The misleading expectation is that reading an atom ID only returns an existing scalar. In the pinned 2026 `gciBody_w::getAtomId`, a missing pointer-list value can cause integer field one to be sign-extended and installed into pointer field zero before the ID is returned.

The complete original backend span is `[0x32f80d60,0x32f80ee6)`, SHA-256 `d95a0548a4bdfaf1ca6637ae67034342500557f56f84a0745aff544e2f9d1eec`, in `sldgciParau.dll` SHA-256 `96f244063a5e8badc547fca3655506ae8eb99197653168efa232d775b55b96ce`. A missing attribute or first-integer `-1` sentinel returns zero. Existing pointer entries take a different branch.

For a read-only diagnostic, record the result of the application's existing getter call; do not call an additional getter as an observer. Also retain the original raw handle domain: `gcBody_w` can be a small opaque kernel identity rather than a heap object.

The [body-to-atom record](../../../../../../re/solidworks/records/PartBodyAtomBinding2026.md) binds the concrete caller, return-register roles and later feature/output membership gates. This source result does not establish the cause of an individual cold-open failure or authorize any live state change.
