from __future__ import annotations

# large graphs need evidence that reference widths follow actual node indexes
KWidths = """
Report['last_reference_tags'] = [Point['h2']['idx'], Line['fc8_s']]
Report['last_reference_indices'] = [Second, Start]
Report['late_reference_tag'] = int.from_bytes(LateBytes[:2], 'little')
Report['late_reference_bytes'] = len(LateBytes)
print(DumpJson(Report))
"""
