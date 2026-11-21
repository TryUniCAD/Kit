from __future__ import annotations

# configuration loading needs its owning header because direct archive references derive from header state
KBaseHeader = """
BaseHeader = NewHeader(
    next_id=BaseGraph.next_persistent_id,
    user_names=(NamePrefix + "author",),
    company_names=(NamePrefix + "company",),
    revision_logs=BaseLogs,
    created_at=1700000000,
    modified_at=1700000001,
    updated_at=1700000001,
    model_present=True,
    component_count=0,
    update_stamp=101,
    body_stamp=101,
    license_flags=0,
    license_type=0,
)
StreamMap["Contents/Config-0-ModelHeader"] = StoreRooted(
    StreamDoc("rooted", {"base": 1}, [BaseHeader]), CodecReg, 19000
)
"""
