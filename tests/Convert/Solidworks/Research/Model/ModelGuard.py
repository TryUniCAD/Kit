from __future__ import annotations

# the audit must precede builder imports because construction must expose every data access
KGuard = """
from tests.Convert.Solidworks.Research.ConstructionGuard import BuildAudit

SchemaDir = WorkRoot / "re" / "tooling" / "sw2026" / "serial" / "defs"
AuditGuard = BuildAudit(SchemaDir)
SystemLib.addaudithook(AuditGuard.InspectEvent)
"""
