# Initialize property codecs before guarded read checks

The guarded public reader replay initializes its supported text codecs before rejecting external file reads. SOLIDWORKS core properties use `utf-8-sig` for XML with an optional byte order mark. Under a fresh Python 3.11 interpreter the codec module can load on its first use, after the guard is already active.

Initialize `utf-8-sig` alongside the existing codecs before enabling the guard. The production reader and its input handling retain their normal behavior. [Revolve process verifier](../../../../../../re/tooling/sw2026/revolve/PublicRead/AuditPublicRevolve01.py)
