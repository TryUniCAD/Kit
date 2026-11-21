# Locked JSON needs exact line endings

Expectation: staging an oracle source-lock JSON preserves the exact bytes bound by native and preparation receipts.

Actual behavior: the Windows author writes CRLF. The repository's automatic LF policy changed the staged end-condition lock from SHA-256 `4df0938264f7761ada1f6fbc10f2335227459e6f03960ab1baa27a0395d395fe` to `e2af9f6d28c5e4b11f63837e63ba039ce25c74fd5a129569f69233c76825106d`. A byte-bound owner receipt would therefore disagree after checkout even though the JSON values match. The mismatch was caught by static comparison of working-tree and staged Git bytes before publication; no archive schema ran.

Workaround: the specific `re/solidworks/v2026/heldout/EndConditionSourceLock.json` path is immutable raw-byte evidence and has the `binary` attribute in `.gitattributes`. Restage it with `git add --renormalize PATH` after changing the attribute. This preserves the original CRLF bytes and original fingerprint, prevents a text merge from modifying the lock and keeps raw CRLF outside source-text whitespace interpretation. Keep source and receipt hashes intact; no general normalization exemption or reconstructed source lock is needed.
