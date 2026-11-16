from __future__ import annotations

# fresh header construction requires authored revision provenance that agrees with the allocated root identifier
KBaseRevision = """
BaseStamp = {
    "status": 0,
    "user_index": 0,
    "company_index": 0,
    "timestamp": 1700000000,
    "comment": NamePrefix + "created",
}
BaseLogs = [{"object_id": BaseGraph.part["f08"], "stamps": [BaseStamp]}]
"""
