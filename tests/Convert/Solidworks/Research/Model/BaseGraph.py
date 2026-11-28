from __future__ import annotations

# the complete owned graph must reach serialization because standalone helper success cannot prove composition
KBaseGraph = """
BaseGraph = NewPartGraph(
    name=NamePrefix + "base part",
    configuration_names=ConfigNames,
    plane_names={AxisName: NamePrefix + AxisName for AxisName in ("z", "y", "x")},
    folder_names={ClassName: NamePrefix + ClassName for ClassName in ClassNames},
    cabinet_name=NamePrefix + "base annotations",
    detail_definitions=BaseStyleData,
    document_units=BaseUserUnits,
    analysis_units=BaseAnalysisUnits,
    hatch_name=NamePrefix + "hatch",
    date_code=2026306,
    parasolid_version=370108,
    created_at=1700000000,
    updated_at=1700000001,
    retain_construction_flag=True,
)
"""
