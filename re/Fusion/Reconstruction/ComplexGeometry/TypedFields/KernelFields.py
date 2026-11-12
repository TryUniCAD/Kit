"""Derive typed subtype field names from ASM kernel save and restore routines.

Usage: python3 KernelFields.py <thin arm64 libASMkern232.dylib>
The slice is Frameworks/ASM/libASMkern232.dylib from the Fusion app bundle, thinned
with `lipo -thin arm64`. For every routine below the script records the address
range, the ordered save/restore calls and the text labels passed to write_logical
and write_id. FIELDS maps each typed field to the call that writes it. A field is
"derived" when a symbol or a label names its content. It is "inferred" when the
kernel only shows the primitive that writes it; such names describe what is stored.
"""
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TYPED = 'src/convert/formats/Fusion/BrepCodec/Journal/Complex/Typed/'
ROUTINES = (
    'subtype_object::save(', 'int_cur::save_common_data(', 'int_cur::restore_common_data(',
    'approx_cur_cache::save(', 'discontinuity_info::save(', 'intcur_cache::save_hap(', 'hap_cache::save(',
    'exp_par_cur::save_data(', 'exp_par_cur::restore_data(', 'exact_int_cur::save_data(', 'exact_int_cur::restore_data(',
    'par_int_cur::save_data(', 'par_int_cur::restore_data(', 'int_int_cur::save_data(', 'spring_int_cur::save_data(',
    'spring_int_cur::restore_data(', 'spl_sur::save_common_data(', 'spl_sur::restore_common_data(', 'approx_sur_cache::save(',
    'exact_spl_sur::save_data(', 'exact_spl_sur::restore_data(', 'blend_support::save_data(', 'curvature_samples::save(',
    'var_radius::save_data(', 'var_rad_edge_offset::save(', 'var_rad_fixed_width::save(', 'var_rad_interp::save(',
    'var_cross_section::save(', 'blend_spl_sur::save_data(', 'blend_spl_sur::restore_data(', 'blend_spl_sur::bl_cache::save_data(',
    'var_blend_spl_sur::save_data(', 'g2_blend_spl_sur::save_data(', 'VBL_SURF::save_data(', 'BDY_GEOM_PCURVE::save(',
    'BDY_GEOM::save(', 'sweep_sur::save_data(', 'profile_manager::save_data(', 'path_manager::save_data(',
    'path_law_manager::save_data(', 'path_2rail_manager::save_data(', 'path_normal_manager::save_data(',
    'path_twist_manager::save_data(', 'loft_spl_sur::save_data(', 'skin_section::save_data(', 'skin_sect_piece::save_data(',
    'bs3_curve_wrapper::save_data(',
)
IDS = ('path_law_manager::id(', 'path_2rail_manager::id(', 'path_normal_manager::id(', 'path_translate_manager::id(',
       'path_twist_manager::id(', 'path_2axis_manager::id(')
KEEP = re.compile(r'write_|read_|save|restore|approx|toleran|magic|fitol|surf_ptr|pcurve::cur|lazy_evaluation|id_upto')
D, I = 'derived', 'inferred'
FIELDS = (
    ('CurveRecords', 'CurveContext', 'context', (
        ('Revision', 'subtype_object::save', 'write_long, version gated, before save_data', I, 'Only the primitive is visible. The corpus value is 23100.'),
        ('ApproxCurve', 'approx_cur_cache::save', 'bs3_curve_save', D, 'Restore passes the bs3 curve to approx_cur_cache::set_approx.'),
        ('FitTolerance', 'approx_cur_cache::save', 'write_real after the bs3 curve', I, 'Restore passes it with the curve to set_approx; the summary branch calls set_tolerance.'),
        ('FirstSurface', 'int_cur::save_common_data', 'surface::save_surface', D, 'First of two surface saves.'),
        ('SecondSurface', 'int_cur::save_common_data', 'surface::save_surface', D, 'Second of two surface saves.'),
        ('FirstPcurve', 'int_cur::save_common_data', 'bs2_curve_save', D, 'First of two bs2 curve saves.'),
        ('SecondPcurve', 'int_cur::save_common_data', 'bs2_curve_save', D, 'Second of two bs2 curve saves.'),
        ('ParamRange', 'int_cur::save_common_data', 'write_interval, version gated', I, 'Only the interval primitive is visible.'),
        ('Discontinuities', 'discontinuity_info::save', 'three counted write_real lists', D, 'Symbol name.'),
        ('HapCache', 'intcur_cache::save_hap', 'hap_cache::save write_int', D, 'Symbol name.'),
    )),
    ('CurveRecords', 'ExpParCur', 'exp_par_cur', (
        ('Spline', 'exp_par_cur::save_data', 'bs2_curve_save', D, 'The bs2 curve is the parameter-space definition.'),
        ('FitTolerance', 'exp_par_cur::save_data', 'write_real', I, 'Only the real primitive is visible.'),
        ('Surface', 'exp_par_cur::save_data', 'surface::save_surface', D, 'Symbol name.'),
    )),
    ('CurveRecords', 'ExactIntCur', 'exact_int_cur', (
        ('Context', 'exact_int_cur::save_data', 'int_cur::save_common_data', D, 'Symbol name.'),
        ('RangeBounds', 'exact_int_cur::save_data', 'write_interval, version gated', I, 'Legacy restore defaults it to the interval (1, 0).'),
        ('LowEndForm', 'exact_int_cur::save_data', 'first write_enum', I, 'Legacy restore sets 2 when the stored low end exceeds the cached low end, else 0.'),
        ('HighEndForm', 'exact_int_cur::save_data', 'second write_enum', I, 'Legacy restore sets 2 when the stored high end is below the cached high end, else 0.'),
    )),
    ('CurveRecords', 'ParIntCur', 'par_int_cur', (
        ('Context', 'par_int_cur::save_data', 'int_cur::save_common_data', D, 'Symbol name.'),
        ('IsSurfOne', 'par_int_cur::save_data', "write_logical false 'surf2' true 'surf1'", D, 'Text labels.'),
        ('ExtraFlag', 'par_int_cur::save_data', "write_logical false 'F' true 'T'", I, 'Generic labels only.'),
    )),
    ('CurveRecords', 'IntIntCur', 'int_int_cur', (
        ('Context', 'int_int_cur::save_data', 'branch to int_cur::save_common_data', D, 'Symbol name.'),
    )),
    ('CurveRecords', 'SpringIntCur', 'spring_int_cur', (
        ('Context', 'spring_int_cur::save_data', 'int_cur::save_common_data', D, 'Symbol name.'),
        ('SpringSide', 'spring_int_cur::save_data', 'write_enum', I, "An older branch writes write_logical false 'right' true 'left' instead."),
    )),
    ('SurfaceRecords', 'SplineCommon', 'tail', (
        ('ApproxSurface', 'approx_sur_cache::save', 'bs3_surface_save', D, 'Restore passes it to approx_sur_cache::set_approx.'),
        ('FitTolerance', 'approx_sur_cache::save', 'write_real after the surface', I, 'Restore passes it with the surface to set_approx; the summary branch calls set_tolerance.'),
        ('FirstBreaks', 'spl_sur::save_common_data', 'discontinuity_info::save', D, 'First of two discontinuity saves.'),
        ('SecondBreaks', 'spl_sur::save_common_data', 'discontinuity_info::save', D, 'Second of two discontinuity saves.'),
    )),
    ('SurfaceRecords', 'ExactSplSur', 'exact_spl_sur', (
        ('Revision', 'subtype_object::save', 'write_long, version gated', I, 'Only the primitive is visible.'),
        ('Common', 'exact_spl_sur::save_data', 'spl_sur::save_common_data', D, 'Symbol name.'),
        ('FirstRange', 'exact_spl_sur::save_data', 'first write_interval', I, 'Restore compares it with a component of bs3_surface_range when RangeForm is nonzero.'),
        ('SecondRange', 'exact_spl_sur::save_data', 'second write_interval', I, 'Restore compares it with a component of bs3_surface_range when RangeForm is nonzero.'),
        ('RangeForm', 'exact_spl_sur::save_data', 'write_enum', I, 'A nonzero value makes restore run the range comparison.'),
    )),
    ('BlendParts', 'BlendSupport', 'side', (
        ('SupportKind', 'blend_support::save_data', 'write_string', D, 'The routine selects the string among blend support class names.'),
        ('Surface', 'blend_support::save_data', 'surface::save_surface', D, 'Symbol name.'),
        ('Curve', 'blend_support::save_data', 'curve::save_curve', D, 'Symbol name.'),
        ('FirstPcurve', 'blend_support::save_data', 'bs2_curve_save', D, 'First bs2 curve save.'),
        ('Position', 'blend_support::save_data', 'write_position', D, 'Primitive kind.'),
        ('SecondPcurve', 'blend_support::save_data', 'bs2_curve_save, conditional', D, 'Second bs2 curve save.'),
        ('SampleCount', 'curvature_samples::save', 'write_int', I, 'curvature_samples::save starts with write_int and a version gated write_int follows it.'),
        ('ThirdPcurve', 'blend_support::save_data', 'bs2_curve_save, version gated', D, 'Third bs2 curve save.'),
    )),
    ('BlendParts', 'OffsetRadius', 'offset', (
        ('RadiusKind', 'var_rad_edge_offset::save / var_rad_fixed_width::save', "write_id 'edge_offset' or 'fixed_width'", D, 'Text identifiers.'),
        ('LeadEnum', 'var_radius::save_data', 'write_enum', I, 'Only the enum primitive is visible.'),
        ('IsCalibrated', 'var_radius::save_data', "write_logical false 'uncalibrated' true 'calibrated'", D, 'Text labels.'),
        ('FirstParam', 'var_radius::save_data', 'first write_real', I, 'Only the real primitive is visible.'),
        ('SecondParam', 'var_radius::save_data', 'second write_real', I, 'Only the real primitive is visible.'),
        ('OffsetValue', 'var_rad_edge_offset::save', 'third write_real', I, 'Only the real primitive is visible.'),
    )),
    ('BlendParts', 'InterpRadius', 'blend:interp', (
        ('LeadEnum', 'var_rad_interp::save', 'write_enum', I, 'Only the enum primitive is visible.'),
        ('IsCalibrated', 'var_rad_interp::save', "write_logical false 'uncalibrated' true 'calibrated'", D, 'Text labels.'),
        ('FirstParam', 'var_rad_interp::save', 'first write_real', I, 'Only the real primitive is visible.'),
        ('SecondParam', 'var_rad_interp::save', 'second write_real', I, 'Only the real primitive is visible.'),
        ('Spline', 'var_rad_interp::save', 'bs2_curve_save', D, 'Primitive kind.'),
        ('SampleForm', 'var_rad_interp::save', 'write_enum', I, 'Only the enum primitive is visible.'),
        ('Samples', 'var_rad_interp::save', 'write_int count, then four write_real, write_position, write_vector', D, 'Counted list.'),
    )),
    ('BlendParts', 'InterpSample', 'blend:interp sample', (
        ('Values', 'var_rad_interp::save', 'four write_real', I, 'Only the real primitive is visible.'),
        ('Position', 'var_rad_interp::save', 'write_position', D, 'Primitive kind.'),
        ('Direction', 'var_rad_interp::save', 'write_vector', I, 'Only the vector primitive is visible.'),
    )),
    ('BlendParts', 'BlendFrame', 'KBlendFrame', (
        ('FirstRange', 'blend_spl_sur::save_data', 'write_interval of member +0x2f0', I, 'Only the interval primitive is visible.'),
        ('SecondRange', 'blend_spl_sur::save_data', 'write_interval of member +0x368', I, 'Only the interval primitive is visible.'),
        ('FirstByte', 'blend_spl_sur::save_data', 'write_int of byte member +0x308', I, 'A byte member written as an integer.'),
        ('ReqTolerance', 'blend_spl_sur::save_data', 'approx_sur_cache::get_req_tolerance, write_real', D, 'Symbol name.'),
        ('FitTolerance', 'blend_spl_sur::save_data', 'approx_sur_cache::get_tolerance, write_real', D, 'Symbol name.'),
        ('SecondByte', 'blend_spl_sur::save_data', 'write_int of byte member +0x320', I, 'A byte member written as an integer.'),
        ('Common', 'blend_spl_sur::save_data', 'spl_sur::save_common_data', D, 'Symbol name.'),
        ('HapCaches', 'blend_spl_sur::bl_cache::save_data', 'hap_cache::save three times', D, 'Symbol name.'),
    )),
    ('BlendRecords', 'SrfSrfBlend', 'srf_srf_v_bl_spl_sur', (
        ('Revision', 'subtype_object::save', 'write_long, version gated', I, 'Only the primitive is visible.'),
        ('FirstSupport', 'blend_spl_sur::save_data', 'blend_support::save_data', D, 'First support save.'),
        ('SecondSupport', 'blend_spl_sur::save_data', 'blend_support::save_data', D, 'Second support save.'),
        ('BlendCurve', 'blend_spl_sur::save_data', 'curve::save_curve', D, 'The curve saved by blend_spl_sur; its role is not named.'),
        ('FirstValue', 'blend_spl_sur::save_data', 'write_real of member +0x330', I, 'Only the real primitive is visible.'),
        ('SecondValue', 'blend_spl_sur::save_data', 'write_real of member +0x338', I, 'Only the real primitive is visible.'),
        ('RadiusForm', 'blend_spl_sur::save_data', 'write_enum before the radius saves', I, 'Restore reads it, then calls restore_radius twice; value 1 carries two radii in the corpus.'),
        ('FirstRadius', 'blend_spl_sur::restore_data', 'restore_radius', D, 'Symbol name.'),
        ('SecondRadius', 'blend_spl_sur::restore_data', 'restore_radius', D, 'Symbol name.'),
        ('Frame', 'blend_spl_sur::save_data', 'intervals, tolerances, spl_sur::save_common_data, bl_cache', D, 'See BlendFrame.'),
        ('VarBlendCurve', 'var_blend_spl_sur::save_data', 'curve::save_curve', D, 'The curve saved by var_blend_spl_sur.'),
        ('IsConvex', 'var_blend_spl_sur::save_data', "write_logical false 'concave' true 'convex'", D, 'Text labels.'),
        ('IsEnvelope', 'var_blend_spl_sur::save_data', "write_logical false 'rb_snapshot' true 'rb_envelope'", D, 'Text labels.'),
        ('VarBlendRange', 'var_blend_spl_sur::save_data', 'write_interval', I, 'Only the interval primitive is visible.'),
        ('VarBlendSpline', 'var_blend_spl_sur::save_data', 'first bs3_curve_save', D, 'Primitive kind. The second bs3 curve is fixed null in the grammar.'),
    )),
    ('BlendRecords', 'GtwoBlend', 'g2_blend_spl_sur', (
        ('Revision', 'subtype_object::save', 'write_long, version gated', I, 'Only the primitive is visible.'),
        ('FirstGtwoReal', 'g2_blend_spl_sur::save_data', 'first write_real', I, 'Only the real primitive is visible.'),
        ('SecondGtwoReal', 'g2_blend_spl_sur::save_data', 'second write_real', I, 'Only the real primitive is visible.'),
        ('FirstSupport', 'blend_spl_sur::save_data', 'blend_support::save_data', D, 'First support save.'),
        ('SecondSupport', 'blend_spl_sur::save_data', 'blend_support::save_data', D, 'Second support save.'),
        ('BlendCurve', 'blend_spl_sur::save_data', 'curve::save_curve', D, 'The curve saved by blend_spl_sur.'),
        ('FirstValue', 'blend_spl_sur::save_data', 'write_real of member +0x330', I, 'Only the real primitive is visible.'),
        ('SecondValue', 'blend_spl_sur::save_data', 'write_real of member +0x338', I, 'Only the real primitive is visible.'),
        ('Frame', 'blend_spl_sur::save_data', 'intervals, tolerances, spl_sur::save_common_data, bl_cache', D, 'See BlendFrame.'),
    )),
    ('VertexRecords', 'VblBoundary', 'vertexblend', (
        ('IsCross', 'BDY_GEOM::save', "write_logical false 'non_cross' true 'cross'", D, 'Text labels.'),
        ('MagicVector', 'BDY_GEOM::save', 'BDY_GEOM::magic, write_vector', D, 'Symbol name.'),
        ('FirstSmooth', 'BDY_GEOM::save', "write_logical false 'non_smooth' true 'smooth'", D, 'Text labels; which end it covers is not named.'),
        ('SecondSmooth', 'BDY_GEOM::save', "write_logical false 'non_smooth' true 'smooth'", D, 'Text labels; which end it covers is not named.'),
        ('BoundaryValue', 'BDY_GEOM::save', 'write_real of member +0x50', I, 'Only the real primitive is visible.'),
        ('Surface', 'BDY_GEOM_PCURVE::save', 'pcurve::surf_ptr, surface::save_surface', D, 'Symbol names.'),
        ('Spline', 'BDY_GEOM_PCURVE::save', 'pcurve::cur, bs2_curve_save', D, 'Symbol names.'),
        ('IsReversed', 'BDY_GEOM_PCURVE::save', "write_logical false 'forward' true 'reversed'", D, 'Text labels.'),
        ('FitTolerance', 'BDY_GEOM_PCURVE::save', 'pcurve::fitol, write_real', D, 'Symbol name.'),
    )),
    ('VertexRecords', 'VblSurf', 'VBL_SURF', (
        ('Revision', 'subtype_object::save', 'write_long, version gated', I, 'Only the primitive is visible.'),
        ('Boundaries', 'VBL_SURF::save_data', "write_int count, then virtual saves; BDY_GEOM_PCURVE::save writes write_id 'pcurve'", D, 'Counted list.'),
        ('TrailInt', 'VBL_SURF::save_data', 'write_int after the list', I, 'Only the integer primitive is visible.'),
        ('FitTolerance', 'VBL_SURF::save_data', 'approx_sur_cache::get_tolerance, write_real', D, 'Symbol name.'),
    )),
    ('SweepRecords', 'SweepSur', 'sweep_sur', (
        ('Revision', 'subtype_object::save', 'write_long, version gated', I, 'Only the primitive is visible.'),
        ('IsOnXy', 'sweep_sur::save_data', "write_logical false 'not_on' true 'on_xy'", D, 'Text labels.'),
        ('ProfileId', 'sweep_sur::save_data', 'profile_manager::id_upto_217, write_int', D, 'Symbol name.'),
        ('Profile', 'profile_manager::save_data', 'virtual profile save', D, 'Symbol name.'),
        ('Path', 'sweep_sur::save_data', 'path manager id write_int, then virtual path save', D, 'Ids 1, 2, 3 and 5 come from the path manager id() constants.'),
        ('Common', 'sweep_sur::save_data', 'spl_sur::save_common_data', D, 'Symbol name.'),
    )),
    ('SweepRecords', 'SweepProfile', 'sweep_sur profile', (
        ('Curve', 'profile_manager::save_data', 'curve::save_curve', D, 'Symbol name.'),
        ('ParamRange', 'profile_manager::save_data', 'write_interval', I, 'Only the interval primitive is visible.'),
        ('PlanarFrame', 'profile_manager::save_data', "write_logical false 'not_planar' true 'is_planar', then write_position and write_vector", D, 'Text labels gate the pair.'),
        ('Position', 'profile_manager::save_data', 'write_position, version gated', D, 'Primitive kind.'),
        ('FrameMatrix', 'profile_manager::save_data', 'write_matrix', D, 'Primitive kind.'),
    )),
    ('SweepPaths', 'PathHead', 'railhead', (
        ('IsNoZ', 'path_manager::save_data', "write_logical false 'has_z' true 'no_z'", D, 'Text labels.'),
        ('PathCurve', 'path_manager::save_data', 'curve::save_curve', D, 'Symbol name.'),
        ('PathRange', 'path_manager::save_data', 'write_interval', I, 'Only the interval primitive is visible.'),
        ('PathReal', 'path_manager::save_data', 'write_real', I, 'Only the real primitive is visible.'),
        ('HasScale', 'path_manager::save_data', "write_logical false 'no_scale' true 'has_scale'", D, 'Text labels.'),
    )),
    ('SweepPaths', 'LawPath', 'rail:1', (
        ('Header', 'path_law_manager::save_data', 'path_manager::save_data', D, 'Symbol name.'),
        ('Formula', 'path_law_manager::save_data', 'save_law', D, 'Symbol name.'),
        ('IsTwistPeriodic', 'path_law_manager::save_data', "write_logical false 'no_twist_periodic' true 'yes_twist_periodic'", D, 'Text labels.'),
    )),
    ('SweepPaths', 'RailPath', 'rail:2', (
        ('Header', 'path_2rail_manager::save_data', 'path_manager::save_data', D, 'Symbol name.'),
        ('IsNoRail', 'path_2rail_manager::save_data', "write_logical false 'has_rail' true 'no_rail'", D, 'Text labels.'),
        ('RailCurve', 'path_2rail_manager::save_data', 'curve::save_curve', D, 'Symbol name.'),
        ('RailRange', 'path_2rail_manager::save_data', 'write_interval', I, 'Only the interval primitive is visible.'),
        ('CrossValues', 'path_2rail_manager::save_data', 'virtual call after the interval', I, 'The grammar reads two counted real lists here.'),
        ('TrailFlags', 'path_2rail_manager::save_data', "logicals; the last two kernel labels are 'x_scaling' and 'y_scaling'", I, 'The grammar has three flags where the kernel shows a position and two logicals.'),
    )),
    ('SweepPaths', 'NormalPath', 'rail:3', (
        ('Header', 'path_normal_manager::save_data', 'path_manager::save_data', D, 'Symbol name.'),
        ('Surface', 'path_normal_manager::save_data', 'surface::save_surface', D, "Symbol name. The following 'has_pcurve' logical is fixed false in the grammar."),
        ('TrailFlag', 'path_normal_manager::save_data', "next logical, kernel labels 'no_svec' and 'has_svec'", I, 'Mapped by order only.'),
    )),
    ('SweepPaths', 'TwistPath', 'rail:5', (
        ('Header', 'path_twist_manager::save_data', 'path_manager::save_data', D, 'Symbol name.'),
        ('InnerPath', 'path_twist_manager::save_data', 'write_int id, then virtual path save', D, 'Nested path manager.'),
        ('Position', 'path_twist_manager::save_data', 'write_position', D, 'Primitive kind.'),
        ('PathVector', 'path_twist_manager::save_data', 'write_vector', I, 'Only the vector primitive is visible.'),
        ('FirstReal', 'path_twist_manager::save_data', 'first write_real', I, 'Only the real primitive is visible.'),
        ('SecondReal', 'path_twist_manager::save_data', 'second write_real', I, 'Only the real primitive is visible.'),
    )),
    ('LoftRecords', 'LoftSplSur', 'loft_spl_sur', (
        ('Revision', 'subtype_object::save', 'write_long, version gated', I, 'Only the primitive is visible.'),
        ('FirstSections', 'loft_spl_sur::save_data', 'write_int count, then write_real and skin_section::save_data', D, 'Symbol name.'),
        ('SecondSections', 'loft_spl_sur::save_data', 'write_int count, then write_real and skin_section::save_data', D, 'Symbol name.'),
        ('FirstRange', 'loft_spl_sur::save_data', 'first write_interval', I, 'Only the interval primitive is visible.'),
        ('SecondRange', 'loft_spl_sur::save_data', 'second write_interval', I, 'Only the interval primitive is visible.'),
        ('LoftFlags', 'loft_spl_sur::save_data', "four write_logical with labels 'F' and 'T'", I, 'Generic labels only.'),
        ('TrailInts', 'loft_spl_sur::save_data', 'two write_int', I, 'Only the integer primitive is visible.'),
        ('Common', 'loft_spl_sur::save_data', 'spl_sur::save_common_data', D, 'Symbol name.'),
    )),
    ('LoftRecords', 'LoftSection', 'section', (
        ('SectionValue', 'loft_spl_sur::save_data', 'write_real before each skin_section', I, 'Only the real primitive is visible.'),
        ('Pieces', 'skin_section::save_data', 'write_int count, then skin_sect_piece::save_data', D, 'Symbol name.'),
        ('SectionCurve', 'skin_section::save_data', 'curve::save_curve', D, 'Symbol name.'),
        ('Wrappers', 'skin_section::save_data', 'write_int count, then bs3_curve_wrapper::save_data', D, 'bs3_curve_wrapper::save_data branches to bs3_curve_save.'),
        ('TrailInt', 'skin_section::save_data', 'final write_int', I, 'Only the integer primitive is visible.'),
    )),
    ('LoftRecords', 'LoftPiece', 'member', (
        ('PieceKind', 'skin_sect_piece::save_data', 'write_int', D, 'The value selects the piece layout.'),
        ('Curve', 'skin_sect_piece::save_data', 'curve::save_curve', D, 'Symbol name.'),
        ('Surface', 'skin_sect_piece::save_data', 'boundary_geometry_nontol::save_data_and_normal', I, 'Mapped by grammar order.'),
        ('FirstPcurve', 'skin_sect_piece::save_data', 'boundary_geometry_nontol::save_data_and_normal', I, 'Mapped by grammar order.'),
        ('SecondPcurve', 'skin_sect_piece::save_data', 'boundary_geometry_nontol::save_data_and_normal', I, 'Mapped by grammar order.'),
        ('PieceFlag', 'skin_sect_piece::save_data', 'logical in the boundary geometry block', I, 'Mapped by grammar order.'),
        ('ReparamInt', 'skin_sect_piece::save_data', 'loft_reparam::save', D, 'Symbol name.'),
        ('Reparam', 'skin_sect_piece::save_data', 'loft_reparam::save', D, 'Symbol name.'),
        ('PieceVector', 'skin_sect_piece::save_data', "write_logical 'F'/'T' gating write_vector", I, 'Only the vector primitive is visible.'),
    )),
)


def symbols(path):
    output = subprocess.run(['nm', '-n', path], capture_output=True, text=True, check=True).stdout
    rows = [(int(found.group(1), 16), found.group(2)) for found in map(re.compile(r'^([0-9a-f]{16}) [tT] (.+)$').match, output.splitlines()) if found]
    names = subprocess.run(['c++filt'], input='\n'.join(name for _, name in rows), capture_output=True, text=True, check=True).stdout.splitlines()
    return [(address, name) for (address, _), name in zip(rows, names)]


def sections(path):
    rows, current = [], {}
    for line in subprocess.run(['otool', '-l', path], capture_output=True, text=True, check=True).stdout.splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[0] in ('sectname', 'segname', 'addr', 'size', 'offset'):
            current[parts[0]] = parts[1]
            if parts[0] == 'offset' and 'sectname' in current:
                rows.append((current['sectname'], int(current['addr'], 16), int(current['size'], 16), int(current['offset'])))
                current = {}
    return rows


def cstring(data, table, address):
    for name, start, size, offset in table:
        if start <= address < start + size and 'cstring' in name:
            position = offset + address - start
            return data[position:data.index(b'\0', position)].decode('latin-1')
    return None


def disassemble(path, start, stop):
    return subprocess.run(['xcrun', 'llvm-objdump', '--disassemble', '--demangle', '--no-show-raw-insn', f'--start-address={start:#x}', f'--stop-address={stop:#x}', path], capture_output=True, text=True, check=True).stdout


def routine(path, data, table, start, stop):
    calls, labels, pages = [], [], {}
    for line in disassemble(path, start, stop).splitlines():
        found = re.search(r'^\s*[0-9a-f]+:\s+(\S+)\s*(.*)$', line)
        if not found:
            continue
        opcode, rest = found.groups()
        page = re.match(r'(x\d+), (0x[0-9a-f]+)', rest) if opcode == 'adrp' else None
        offset = re.match(r'(x\d+), (x\d+), #(0x[0-9a-f]+)', rest) if opcode == 'add' else None
        target = re.search(r'<([^>+]+)>', rest) if opcode in ('bl', 'b') else None
        if page:
            pages[page.group(1)] = int(page.group(2), 16)
        elif offset and offset.group(2) in pages:
            pages[offset.group(1)] = pages[offset.group(2)] + int(offset.group(3), 16)
            text = cstring(data, table, pages[offset.group(1)])
            if text and text.isprintable() and 0 < len(text) < 40:
                labels.append(text)
                calls.append('label:' + text)
        elif target and KEEP.search(target.group(1)):
            calls.append(re.sub(r'\(.*', '', target.group(1)))
    return calls, labels


def identity(path, start):
    text = disassemble(path, start, start + 16)
    found = re.search(r'mov\s+w0, #(0x[0-9a-f]+|\d+)', text)
    return int(found.group(1), 0) if found else None


def main():
    path = sys.argv[1]
    data = Path(path).read_bytes()
    table = sections(path)
    rows = symbols(path)
    report = dict(slice=dict(path='Autodesk Fusion.app/Contents/Frameworks/ASM/libASMkern232.dylib (lipo -thin arm64)', sha256=hashlib.sha256(data).hexdigest()), routines=[], pathIds={}, fields=[])
    for prefix in ROUTINES:
        position = next(index for index, (_, name) in enumerate(rows) if name.startswith(prefix))
        start, name = rows[position]
        stop = next(address for address, _ in rows[position + 1:] if address > start)
        calls, labels = routine(path, data, table, start, stop)
        report['routines'].append(dict(symbol=name, range=f'{start:#x}-{stop:#x}', calls=calls, labels=labels))
    for prefix in IDS:
        start, name = next((address, name) for address, name in rows if name.startswith(prefix))
        report['pathIds'][name.split('::')[0]] = identity(path, start)
    for module, owner, grammar, fields in FIELDS:
        for field, source, call, status, basis in fields:
            report['fields'].append(dict(module=TYPED + module + '.py', record=owner, grammar=grammar, field=field, routine=source, call=call, status=status, basis=basis))
    report['counts'] = dict(fields=len(report['fields']), derived=sum(item['status'] == D for item in report['fields']), inferred=sum(item['status'] == I for item in report['fields']))
    (HERE / 'KernelFields.json').write_text(json.dumps(report, indent=1) + '\n')
    print(json.dumps(dict(slice=report['slice'], pathIds=report['pathIds'], counts=report['counts']), indent=1))


if __name__ == '__main__':
    main()
