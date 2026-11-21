# Add a SOLIDWORKS imported body source protocol

The [source protocol](../../../../re/tooling/sw2026/imported_body_source/README.md)
authors a checked temporary modeler solid as a native imported feature on
SOLIDWORKS 2026 SP05.2. It prepares one disclosed box and two guest-private
held-out boxes whose source and measurement identities can be locked by hash.

The runner uses fresh SOLIDWORKS processes and healthy bracketing controls.
It measures topology, body ownership, volume, area and centre of mass before
save and after a fresh reopen. The documented 2026 API and existing oracle
control code define this route. Native execution and resulting receipts remain
pending with the oracle owner.

The scope is source authoring. Writer support and conversion acceptance
remain open under [PR #121](https://github.com/TryUniCAD/Kit/pull/121).
