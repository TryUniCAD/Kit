# Local control parts for file-driven decoding

Supply a local SOLIDWORKS part with `--control <path>`. The decoder inspects its part metadata, configuration and resolved feature records, rejects duplicate resolved streams, and snapshots its contents for successive reader passes. It accepts up to 32 controls, each at most 16 MiB, with a 64 MiB combined input and control budget.

Only registered discovery hashes can contribute training evidence. An unclassified or reserved control appears in the report with `eligible_for_discovery` set to false. See [discovery control eligibility](DiscoveryControlEligibility.md).
