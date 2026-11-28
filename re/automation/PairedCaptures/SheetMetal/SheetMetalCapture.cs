using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Web.Script.Serialization;
using SolidWorks.Interop.sldworks;
using SolidWorks.Interop.swconst;

public static class SheetMetalCapture
{
    const double Mm = .001;
    const double PositionTolerance = 2e-7;
    static readonly JavaScriptSerializer Json = new JavaScriptSerializer { MaxJsonLength = 1 << 24 };

    static Dictionary<string, object> Row(params object[] entries)
    {
        var result = new Dictionary<string, object>();
        for (int i = 0; i < entries.Length; i += 2) result.Add((string)entries[i], entries[i + 1]);
        return result;
    }

    static Dictionary<string, object> Object(object value) { return (Dictionary<string, object>)value; }
    static object[] Items(object value) { return value == null ? new object[0] : ((Array)value).Cast<object>().ToArray(); }
    static double Number(object value) { return Convert.ToDouble(value); }
    static double[] Numbers(object value) { return Items(value).Select(Number).ToArray(); }
    static double Length(Dictionary<string, object> row, string name) { return Number(row[name]) * Mm; }
    static bool Near(double actual, double expected, double tolerance = PositionTolerance) { return Math.Abs(actual - expected) <= tolerance; }

    static void Check(bool passed, string message)
    {
        if (!passed) throw new InvalidOperationException(message);
    }

    static Dictionary<string, object> Archive(string path)
    {
        using (var stream = File.OpenRead(path))
        using (var sha = SHA256.Create())
            return Row("file", Path.GetFileName(path), "size_bytes", stream.Length,
                "sha256", BitConverter.ToString(sha.ComputeHash(stream)).Replace("-", "").ToLowerInvariant());
    }

    static byte[] Reference(IModelDoc2 doc, object item)
    {
        return item == null ? null : doc.Extension.GetPersistReference3(item) as byte[];
    }

    static string Identity(IModelDoc2 doc, object item)
    {
        var reference = Reference(doc, item);
        return reference == null || reference.Length == 0 ? null : Convert.ToBase64String(reference);
    }

    static IFeature[] Features(IModelDoc2 doc)
    {
        var result = new List<IFeature>();
        for (var feature = ((IPartDoc)doc).FirstFeature() as IFeature; feature != null; feature = feature.GetNextFeature() as IFeature)
        {
            Check(result.Count < 1024, "Feature tree top-level chain did not terminate");
            AddFeature(result, feature, 0);
        }
        return result.ToArray();
    }

    static void AddFeature(List<IFeature> result, IFeature feature, int depth)
    {
        Check(depth <= 16 && result.Count < 1024, "Feature tree subfeature chain did not terminate");
        result.Add(feature);
        for (var child = feature.GetFirstSubFeature() as IFeature; child != null; child = child.GetNextSubFeature() as IFeature)
            AddFeature(result, child, depth + 1);
    }

    static IBody2[] Bodies(IModelDoc2 doc)
    {
        return Items(((IPartDoc)doc).GetBodies2((int)swBodyType_e.swSolidBody, false)).Cast<IBody2>().ToArray();
    }

    static double[][] Bounds(IBody2 body)
    {
        var bounds = new[] { new double[3], new double[3] };
        for (int side = 0; side < 2; side++)
        for (int axis = 0; axis < 3; axis++)
        {
            var direction = new double[3];
            direction[axis] = side == 0 ? -1 : 1;
            double x, y, z;
            Check(body.GetExtremePoint(direction[0], direction[1], direction[2], out x, out y, out z),
                "Could not measure a solid body's extreme point");
            bounds[side][axis] = new[] { x, y, z }[axis];
        }
        return bounds;
    }

    static Dictionary<string, object> BodyRow(IModelDoc2 doc, IBody2 body)
    {
        var mass = Numbers(body.GetMassProperties(1));
        Check(mass.Length == 12 && mass.All(value => !Double.IsNaN(value) && !Double.IsInfinity(value)) && mass[3] > 0,
            "Could not measure a valid solid body");
        return Row("name", body.Name, "persist_reference", Identity(doc, body), "bounds_m", Bounds(body),
            "centroid_m", mass.Take(3).ToArray(), "volume_m3", mass[3], "surface_area_m2", mass[4]);
    }

    static Dictionary<string, object> FeatureRow(IModelDoc2 doc, IFeature feature)
    {
        bool warning;
        var type = feature.GetTypeName2();
        var code = feature.GetErrorCode2(out warning);
        var suppressed = feature.IsSuppressed();
        Check(code == 0 || suppressed, "Native feature diagnostic " + code + " on " + feature.Name + " (warning=" + warning + ")");
        var result = Row("name", feature.Name, "type", type, "feature_id", feature.GetID(),
            "persist_reference", Identity(doc, feature),
            "suppressed", suppressed, "error", code, "warning", warning, "parents",
            Items(feature.GetParents()).Cast<IFeature>().Select(parent => Row("name", parent.Name,
                "type", parent.GetTypeName2(), "feature_id", parent.GetID(), "persist_reference", Identity(doc, parent))).ToArray());
        if (type == "CutListFolder")
        {
            var folder = feature.GetSpecificFeature2() as IBodyFolder;
            Check(folder != null, "Cut-list feature has no native body folder");
            result.Add("body_members", Items(folder.GetBodies()).Cast<IBody2>().Select(body =>
                Row("name", body.Name, "persist_reference", Identity(doc, body))).ToArray());
        }
        if (type == "SMBaseFlange")
        {
            var definition = feature.GetDefinition() as IBaseFlangeFeatureData;
            Check(definition != null, "Native base flange has no typed definition");
            result.Add("base_flange", Row("thickness_m", definition.Thickness, "bend_radius_m", definition.BendRadius,
                "default_relief", definition.UseDefaultBendRelief, "relief", definition.ReliefType));
        }
        var flat = type == "FlatPattern" ? feature.GetDefinition() as IFlatPatternFeatureData : null;
        if (flat != null)
            result.Add("flat_pattern_fixed_face", Identity(doc, flat.FixedFace2));
        return result;
    }

    static Dictionary<string, object> Observe(IModelDoc2 doc, int expectedSolidCount)
    {
        Check(doc.ForceRebuild3(false), "SOLIDWORKS reported a rebuild failure");
        var bodies = Bodies(doc);
        Check(bodies.Length == expectedSolidCount, "Expected " + expectedSolidCount + " solid bodies, got " + bodies.Length);
        var features = Features(doc);
        var configuration = doc.ConfigurationManager.ActiveConfiguration;
        Check(configuration != null && !String.IsNullOrEmpty(configuration.Name), "Missing active configuration");
        return Row("configuration", configuration.Name, "rebuild", true, "bodies",
            bodies.Select(body => BodyRow(doc, body)).ToArray(), "features",
            features.Select(feature => FeatureRow(doc, feature)).ToArray());
    }

    static double[] InSketch(ISldWorks app, ISketch sketch, double[] xy, double worldZ)
    {
        var utility = (IMathUtility)app.GetMathUtility();
        var point = (IMathPoint)utility.CreatePoint(new[] { xy[0] * Mm, xy[1] * Mm, worldZ });
        var projected = (double[])point.IMultiplyTransform(sketch.ModelToSketchTransform).ArrayData;
        Check(Near(projected[2], 0), "The world XY control does not lie on the selected datum");
        return projected;
    }

    static double[][] DesiredBounds(Dictionary<string, object> body)
    {
        var low = Numbers(body["low"]);
        var high = Numbers(body["high"]);
        return new[] { new[] { low[0] * Mm, low[1] * Mm, 0 },
            new[] { high[0] * Mm, high[1] * Mm, Length(body, "thickness_mm") } };
    }

    static bool HasBounds(IBody2 body, double[][] desired)
    {
        var actual = Bounds(body);
        return actual.Zip(desired, (a, b) => a.Zip(b, (value, expected) => Near(value, expected)).All(v => v)).All(v => v);
    }

    static object Diagnostic(Func<object> measure)
    {
        try { return measure(); }
        catch (Exception error)
        {
            var cause = error.GetBaseException();
            return Row("measurement_error", cause.GetType().Name, "hresult", cause.HResult, "message", cause.Message);
        }
    }

    static Dictionary<string, object> BaseProfile(ISldWorks app, ISketch sketch)
    {
        var utility = (IMathUtility)app.GetMathUtility();
        var world = sketch.ModelToSketchTransform.IInverse();
        var origin = (IMathPoint)utility.CreatePoint(new[] { 0.0, 0, 0 });
        var normal = (IMathVector)utility.CreateVector(new[] { 0.0, 0, 1 });
        var contours = Items(sketch.GetSketchContours()).Cast<ISketchContour>().ToArray();
        Check(contours.Length == 1 && contours[0].IsClosed(), "The native base-flange sketch did not contain one closed contour");
        return Row("origin_m", origin.IMultiplyTransform(world).ArrayData,
            "normal", normal.IMultiplyTransform(world).ArrayData,
            "model_to_sketch", sketch.ModelToSketchTransform.ArrayData,
            "closed_contour_edges", Items(contours[0].GetSketchSegments()).Cast<ISketchLine>().Select(line =>
            {
                var a = (ISketchPoint)line.GetStartPoint2();
                var b = (ISketchPoint)line.GetEndPoint2();
                return new[] { new[] { a.X, a.Y, a.Z }, new[] { b.X, b.Y, b.Z } };
            }).ToArray());
    }

    static object PlanarFaces(IBody2 body)
    {
        return Items(body.GetFaces()).Cast<IFace2>().Select(face => new { Face = face, Surface = face.IGetSurface() })
            .Where(pair => pair.Surface != null && pair.Surface.IsPlane())
            .Select(pair => Row("face_normal", pair.Face.Normal, "plane_parameters", pair.Surface.PlaneParams,
                "area_m2", pair.Face.GetArea())).ToArray();
    }

    static IFeature CreateThicknessDatum(ISldWorks app, IModelDoc2 doc, double thickness, out Dictionary<string, object> evidence)
    {
        var initial = InsertThicknessDatum(doc, thickness, false);
        var firstFrame = PlaneFrame(app, initial);
        var origin = Numbers(firstFrame["origin_m"]);
        bool reverse = Near(origin[2], -thickness);
        if (reverse)
        {
            doc.ClearSelection2(true);
            Check(initial.Select2(false, 0) && doc.Extension.DeleteSelection2(0), "Could not remove the newly authored mirrored datum");
            initial = InsertThicknessDatum(doc, thickness, true);
        }
        var frame = reverse ? PlaneFrame(app, initial) : firstFrame;
        Check(Near(Numbers(frame["origin_m"])[2], thickness) && SamePoint(Numbers(frame["normal"]), new[] { 0.0, 0, 1 }),
            "Native thickness datum did not bind the desired positive world elevation and frame: " + Json.Serialize(frame));
        initial.Name = "KitThicknessXY";
        evidence = Row("first_frame", firstFrame, "reversed_after_mirrored_measurement", reverse, "final_frame", frame,
            "offset_m", thickness, "source", "Front Plane");
        return initial;
    }

    static IFeature InsertThicknessDatum(IModelDoc2 doc, double thickness, bool reverse)
    {
        doc.ClearSelection2(true);
        Check(doc.Extension.SelectByID2("Front Plane", "PLANE", 0, 0, 0, false, 0, null, 0),
            "Cannot select the world XY datum");
        int relation = (int)swRefPlaneReferenceConstraints_e.swRefPlaneReferenceConstraint_Distance;
        if (reverse) relation |= (int)swRefPlaneReferenceConstraints_e.swRefPlaneReferenceConstraint_OptionFlip;
        var datum = doc.FeatureManager.InsertRefPlane(relation, thickness, 0, 0, 0, 0) as IFeature;
        Check(datum != null, "Cannot create the native offset datum");
        return datum;
    }

    static Dictionary<string, object> PlaneFrame(ISldWorks app, IFeature feature)
    {
        var datum = feature.GetSpecificFeature2() as IRefPlane;
        Check(datum != null, "Native offset feature has no reference plane");
        var utility = (IMathUtility)app.GetMathUtility();
        var origin = (IMathPoint)utility.CreatePoint(new[] { 0.0, 0, 0 });
        var normal = (IMathVector)utility.CreateVector(new[] { 0.0, 0, 1 });
        return Row("origin_m", origin.IMultiplyTransform(datum.Transform).ArrayData,
            "normal", normal.IMultiplyTransform(datum.Transform).ArrayData);
    }

    static Dictionary<string, object> AddBase(ISldWorks app, IModelDoc2 doc, string id, Dictionary<string, object> body,
        IFeature datum, string caseId, string discoveryDirectory)
    {
        doc.ClearSelection2(true);
        Check(datum.Select2(false, 0), "Cannot select the explicit world XY datum");
        doc.SketchManager.InsertSketch(true);
        var sketch = doc.SketchManager.ActiveSketch as ISketch;
        Check(sketch != null, "Could not start base-flange sketch");
        double thickness = Length(body, "thickness_mm");
        var low = InSketch(app, sketch, Numbers(body["low"]), thickness);
        var high = InSketch(app, sketch, Numbers(body["high"]), thickness);
        var segments = Items(doc.SketchManager.CreateCornerRectangle(low[0], low[1], 0, high[0], high[1], 0));
        Check(segments.Length == 4 && segments.All(segment => segment is ISketchLine), "Could not create the four rectangle edges");
        doc.ClearSelection2(true);
        foreach (var segment in segments.Cast<ISketchSegment>())
            Check(segment.Select4(true, null), "Could not select a rectangle segment for constraining");
        doc.SketchAddConstraints("sgFIXED");
        var status = sketch.GetConstrainedStatus();
        Check(status == (int)swConstrainedStatus_e.swFullyConstrained, "Base-flange rectangle constraint status " + status);
        doc.ClearSelection2(true);
        doc.SketchManager.InsertSketch(true);
        var profile = BaseProfile(app, sketch);
        var normal = Numbers(profile["normal"]);
        var origin = Numbers(profile["origin_m"]);
        if (!SamePoint(normal, new[] { 0.0, 0, 1 }) || !Near(origin[2], thickness))
            throw new InvalidOperationException("The measured sketch did not retain the expected positive elevated XY frame: " +
                Json.Serialize(profile));
        var sketchFeature = (IFeature)sketch;
        sketchFeature.Name = "Sketch-" + id;
        Check(sketchFeature.Select2(false, 0), "Could not select the rectangle sketch");

        double radius = Length(body, "radius_mm");
        var allowance = doc.FeatureManager.CreateCustomBendAllowance();
        allowance.Type = (int)swBendAllowanceTypes_e.swBendAllowanceKFactor;
        allowance.KFactor = .5;
        int noRelief = (int)swSheetMetalReliefTypes_e.swSheetMetalReliefNone;
        const bool reverseThickness = true;
        var manager = doc.FeatureManager;
        var typed = manager.CreateDefinition((int)swFeatureNameID_e.swFmBaseFlange) as IBaseFlangeFeatureData;
        Check(typed != null, "Could not create a typed sheet-metal base-flange definition");
        typed.Initialize(false, true, allowance, true, noRelief, false, 0, 0, 0);
        typed.OverrideDefaultSheetMetalParameters = true;
        typed.Thickness = thickness;
        typed.BendRadius = radius;
        typed.ReverseThickness = reverseThickness;
        Check(typed.OverrideDefaultSheetMetalParameters && !typed.UseMaterialSheetMetalParameters &&
            Near(typed.Thickness, thickness) && Near(typed.BendRadius, radius) &&
            typed.ReverseThickness == reverseThickness,
            "The pending base-flange definition did not retain the explicitly initialized parameters");
        var flange = manager.CreateFeature(typed);
        Check(flange != null, "Base flange returned no feature for " + id);
        flange.Name = "Base-" + id;
        Check(doc.ForceRebuild3(false), "Base flange could not rebuild for " + id);
        var expected = DesiredBounds(body);
        var initial = Bodies(doc);
        var evidence = Row("id", id, "requested_thicken_direction", reverseThickness,
            "intended_bounds_m", expected, "profile", profile, "initial_bodies", initial.Select(candidate =>
            Row("name", candidate.Name, "bounds_m", Bounds(candidate), "sheet_metal", candidate.IsSheetMetal(),
                "planar_faces", Diagnostic(() => PlanarFaces(candidate)))).ToArray());
        try
        {
            var definition = flange.GetDefinition() as IBaseFlangeFeatureData;
            Check(definition != null, "Base flange has no typed definition for " + id);
            evidence.Add("initial_reverse_thickness", definition.ReverseThickness);
            evidence.Add("initial_thickness_m", definition.Thickness);
            evidence.Add("initial_radius_m", definition.BendRadius);
            var solid = initial.SingleOrDefault(candidate => HasBounds(candidate, expected));
            if (solid == null || !solid.IsSheetMetal())
            {
                if (discoveryDirectory != null && initial.Any(candidate => candidate.IsSheetMetal()))
                {
                    try { evidence.Add("unqualified_archive", SaveDiagnostic(doc, discoveryDirectory, caseId, id, initial.Length)); }
                    catch (Exception diagnostic)
                    {
                        var cause = diagnostic.GetBaseException();
                        evidence.Add("diagnostic_save_failure", Row("type", cause.GetType().Name,
                            "hresult", cause.HResult, "message", cause.Message));
                    }
                }
                throw new InvalidOperationException("No distinct positive-Z sheet-metal body matched " + id);
            }
            Check(Near(definition.Thickness, thickness) && Near(definition.BendRadius, radius),
                "Base flange did not report the requested thickness and radius for " + id);
            return Row("id", id, "body", BodyRow(doc, solid), "feature", Identity(doc, flange),
                "direction_evidence", evidence,
                "base_flange_authoring", Row("factory", "CreateDefinition(swFmBaseFlange)/CreateFeature",
                    "initialize_arguments", new object[] { false, true,
                        Row("type", allowance.Type, "k_factor", allowance.KFactor), true, noRelief, false, 0, 0, 0 },
                    "override_default_parameters", true, "thickness_m", thickness, "radius_m", radius,
                    "reverse_thickness", reverseThickness),
                "base_readback", Row("thickness_m", definition.Thickness, "bend_radius_m", definition.BendRadius,
                    "reverse_thickness", definition.ReverseThickness),
                "sketch_constraint_status", status);
        }
        catch (Exception error)
        {
            error.GetBaseException().Data["sheet_metal_base_evidence"] = Json.Serialize(evidence);
            throw;
        }
    }

    static double[][] Endpoints(IEdge edge)
    {
        var a = edge.GetStartVertex() as IVertex;
        var b = edge.GetEndVertex() as IVertex;
        return a == null || b == null ? null : new[] { Numbers(a.GetPoint()), Numbers(b.GetPoint()) };
    }

    static bool SamePoint(double[] actual, double[] expected)
    {
        return actual.Length == 3 && actual.Zip(expected, (a, b) => Near(a, b)).All(value => value);
    }

    static bool SameEdge(double[][] actual, double[][] expected)
    {
        return actual != null && ((SamePoint(actual[0], expected[0]) && SamePoint(actual[1], expected[1])) ||
            (SamePoint(actual[1], expected[0]) && SamePoint(actual[0], expected[1])));
    }

    static Dictionary<string, object> AddEdge(IModelDoc2 doc, Dictionary<string, object> body, Dictionary<string, object> request)
    {
        var bounds = DesiredBounds(body);
        var owner = Bodies(doc).Single(candidate => HasBounds(candidate, bounds));
        double x0 = bounds[0][0], x1 = bounds[1][0], y0 = bounds[0][1], y1 = bounds[1][1], z = bounds[1][2];
        var side = (string)request["side"];
        Check(side == "max_x" || side == "max_y", "Unknown recipe edge side");
        var ends = side == "max_x" ? new[] { new[] { x1, y0, z }, new[] { x1, y1, z } } :
            new[] { new[] { x0, y1, z }, new[] { x1, y1, z } };
        var edge = Items(owner.GetEdges()).Cast<IEdge>()
            .Single(candidate => SameEdge(Endpoints(candidate), ends));
        var edgeRef = Identity(doc, edge);
        Check(edgeRef != null, "The chosen upper edge has no persistent reference");
        var topologyOwner = edge.GetBody() as IBody2;
        Check(topologyOwner != null && topologyOwner.Name == owner.Name, "Native selected edge did not report the intended body");
        var witness = Row("source_edge", edgeRef, "endpoints_m", Endpoints(edge), "source_body", BodyRow(doc, owner),
            "edge_owner", Row("name", topologyOwner.Name, "persist_reference", Identity(doc, topologyOwner)),
            "adjacent_faces", Items(edge.GetTwoAdjacentFaces2()).Where(face => face != null).Select(face => Identity(doc, face)).ToArray());
        double angle = Number(request["angle_deg"]) * Math.PI / 180;
        double length = Length(request, "length_mm");
        double radius = Length(body, "radius_mm");
        doc.ClearSelection2(true);
        var profile = doc.IInsertSketchForEdgeFlange((Edge)edge, angle, false);
        Check(profile != null && profile.Select2(false, 0), "Could not create the edge flange profile");
        doc.EditSketch();
        var sketch = doc.SketchManager.ActiveSketch as ISketch;
        Check(sketch != null && ((IEntity)edge).Select4(false, null) && doc.SketchManager.SketchUseEdge(false),
            "Could not project the exact upper edge into the flange profile");
        var projected = Items(sketch.GetSketchSegments()).Cast<ISketchLine>().Single();
        var start = (ISketchPoint)projected.GetStartPoint2();
        var end = (ISketchPoint)projected.GetEndPoint2();
        Check(Near(start.Y, end.Y) && Math.Abs(start.X - end.X) > PositionTolerance,
            "The native edge profile did not orient the projected edge on its X axis");
        var manager = doc.SketchManager;
        var leg = manager.CreateLine(start.X, start.Y, 0, start.X, start.Y + length, 0);
        Check(leg != null && manager.CreateLine(start.X, start.Y + length, 0, end.X, end.Y + length, 0) != null
            && manager.CreateLine(end.X, end.Y + length, 0, end.X, end.Y, 0) != null, "Could not close the projected edge profile");
        Check(((ISketchSegment)leg).Select4(false, null), "Could not select the profile leg for its driving dimension");
        var display = doc.AddDimension2(start.X, start.Y + length / 2, 0) as IDisplayDimension;
        var dimension = display == null ? null : display.GetDimension2(0) as IDimension;
        Check(dimension != null && Near(dimension.SystemValue, length), "Could not bind a driving profile-leg length");
        var dimensionName = dimension.FullName.Split('@')[0] + "@KitEdgeProfile";
        doc.ClearSelection2(true);
        manager.InsertSketch(true);
        profile.Name = "KitEdgeProfile";
        int bendPosition = (int)swFlangePositionTypes_e.swFlangePositionTypeBendOutside;
        int relief = (int)swSheetMetalReliefTypes_e.swSheetMetalReliefNone;
        int sharp = (int)swFlangeDimTypes_e.swFlangeDimTypeInnerVirtualSharp;
        var flange = doc.FeatureManager.InsertSheetMetalEdgeFlange2(new[] { (Edge)edge }, new[] { (Sketch)sketch },
            0, angle, radius, bendPosition, length, relief, 0, 0, 0, sharp, null);
        Check(flange != null, "Edge flange returned no feature");
        flange.Name = "KitEdgeFlange";
        Check(doc.ForceRebuild3(false), "Edge flange could not rebuild");
        witness.Add("feature", Identity(doc, flange));
        witness.Add("profile", Identity(doc, profile));
        witness.Add("profile_dimension", dimensionName);
        witness.Add("edge_flange2_arguments", new object[] { edgeRef, Identity(doc, profile), 0, angle, radius, bendPosition,
            length, relief, 0, 0, 0, sharp, null });
        return witness;
    }

    static Dictionary<string, object> ReadEdge(IModelDoc2 doc, string dimensionName, string sourceEdge,
        double length, double angle, double radius)
    {
        var feature = Features(doc).FirstOrDefault(item => item.Name == "KitEdgeFlange");
        Check(feature != null, "The edge flange feature is missing");
        var dimension = doc.Parameter(dimensionName) as IDimension;
        Check(dimension != null && Near(dimension.SystemValue, length), "Edge flange profile dimension differs from the requested length");
        var data = feature.GetDefinition() as IEdgeFlangeFeatureData;
        Check(data != null, "Missing edge flange definition");
        Check(data.IAccessSelections2((ModelDoc2)doc, null), "Could not access native edge flange selections");
        try
        {
            Check(Near(data.BendAngle, angle, 1e-7) && Near(data.BendRadius, radius) &&
                data.OffsetType == (int)swFlangeOffsetTypes_e.swFlangeOffsetBlind &&
                data.OffsetDimType == (int)swFlangeDimTypes_e.swFlangeDimTypeInnerVirtualSharp &&
                data.PositionType == (int)swFlangePositionTypes_e.swFlangePositionTypeBendOutside &&
                !data.UsePositionOffset && !data.UseDefaultBendRelief &&
                data.AutoReliefType == (int)swSheetMetalReliefTypes_e.swSheetMetalReliefNone,
                "Edge-flange settings differ from the intended blind, inner-sharp, zero-offset, no-relief control");
            var edge = Items(data.Edges).Cast<IEdge>().Single();
            var reference = Reference(doc, edge);
            Check(reference != null && reference.Length > 0, "The selected flange edge has no persistent reference");
            var original = Convert.FromBase64String(sourceEdge);
            Check(doc.Extension.IsSamePersistentID(original, reference) == (int)swObjectEquality.swObjectSame,
                "Native edge flange selection does not match the authored persistent reference");
            var owner = edge.GetBody() as IBody2;
            Check(owner != null, "The resolved edge has no body in the feature definition");
            return Row("edge", Convert.ToBase64String(reference), "source_edge_matches", true, "angle_rad", data.BendAngle,
                "edge_owner", Row("name", owner.Name, "persist_reference", Identity(doc, owner)), "endpoints_m", Endpoints(edge),
                "bend_position", data.PositionType,
                "radius_m", data.BendRadius, "offset_type", data.OffsetType, "native_offset_distance_m", data.OffsetDistance,
                "dimension_type", data.OffsetDimType, "profile_length_m", dimension.SystemValue, "position_offset", data.UsePositionOffset,
                "relief", data.AutoReliefType);
        }
        finally { data.ReleaseSelectionAccess(); }
    }

    static void EditLength(IModelDoc2 doc, string dimensionName, double length)
    {
        var dimension = doc.Parameter(dimensionName) as IDimension;
        Check(dimension != null, "Editable edge-flange dimension could not be found");
        int result = dimension.SetSystemValue3(length, (int)swSetValueInConfiguration_e.swSetValue_InThisConfiguration, null);
        Check(result == (int)swSetValueReturnStatus_e.swSetValue_Successful &&
            doc.ForceRebuild3(false) && Near(dimension.SystemValue, length),
            "Could not edit and rebuild the driving edge-flange profile dimension");
    }

    static T WithDocument<T>(ISldWorks app, IModelDoc2 doc, string expectedReadOnlyPath, Func<IModelDoc2, T> operation)
    {
        Check(doc != null, "No native part document was available");
        Exception original = null;
        try { return operation(doc); }
        catch (Exception error) { original = error; throw; }
        finally
        {
            try
            {
                var title = doc.GetTitle();
                var path = doc.GetPathName();
                bool exactReadback = expectedReadOnlyPath != null && doc.IsOpenedReadOnly() &&
                    String.Equals(path, expectedReadOnlyPath, StringComparison.OrdinalIgnoreCase);
                bool unsavedPrivateAuthoring = expectedReadOnlyPath == null && String.IsNullOrEmpty(path);
                if (app.GetDocumentCount() == 1 && (exactReadback || unsavedPrivateAuthoring))
                    app.QuitDoc(title);
                else
                    app.CloseDoc(title);
                Check(app.GetDocumentCount() == 0, "The owned capture document did not close");
            }
            catch (Exception error)
            {
                if (original == null) throw;
                original.GetBaseException().Data["sheet_metal_close_hresult"] = error.GetBaseException().HResult;
            }
        }
    }

    static IModelDoc2 OpenPart(ISldWorks app, string path, out int errors, out int warnings)
    {
        errors = 0;
        warnings = 0;
        int options = (int)swOpenDocOptions_e.swOpenDocOptions_Silent | (int)swOpenDocOptions_e.swOpenDocOptions_ReadOnly;
        var doc = app.OpenDoc6(path, (int)swDocumentTypes_e.swDocPART, options, "", ref errors, ref warnings) as IModelDoc2;
        Check(doc != null, "Could not open native archive, errors=" + errors + " warnings=" + warnings);
        return doc;
    }

    static void WriteCheckpoint(string path, object report)
    {
        var temporary = path + "." + Guid.NewGuid().ToString("N");
        try
        {
            using (var stream = new FileStream(temporary, FileMode.CreateNew))
            using (var writer = new StreamWriter(stream))
            {
                writer.WriteLine(Json.Serialize(report));
                writer.Flush();
                stream.Flush(true);
            }
            File.Move(temporary, path);
        }
        finally { if (File.Exists(temporary)) File.Delete(temporary); }
    }

    static double TotalVolume(Dictionary<string, object> observation)
    {
        return Items(observation["bodies"]).Sum(body => Number(Object(body)["volume_m3"]));
    }

    static Dictionary<string, object> SaveDiagnostic(IModelDoc2 doc, string directory, string caseId, string baseId, int count)
    {
        Check(caseId == "A-only" || caseId == "A-only-repeat" || caseId == "A-then-B" || caseId == "B-then-A" || caseId == "A-edge",
            "Only a pinned discovery case may emit an unqualified diagnostic archive");
        Check(baseId == "A" || baseId == "B", "Unqualified diagnostic archive has an unknown discovery body");
        var diagnostics = Path.Combine(directory, "unqualified-discovery");
        Check(!Directory.Exists(diagnostics) && !File.Exists(diagnostics), "Refusing to reuse an unqualified archive directory");
        var observed = Diagnostic(() => Observe(doc, count));
        Directory.CreateDirectory(diagnostics);
        var path = Path.Combine(diagnostics, caseId + "-base-" + baseId + ".SLDPRT");
        var save = SaveCopy(doc, path);
        var archive = File.Exists(path) ? Archive(path) : null;
        var report = Row("status", "unqualified_geometry_mismatch", "case", caseId, "base", baseId,
            "archive", archive, "save_as", save,
            "observation", observed);
        WriteCheckpoint(Path.ChangeExtension(path, ".unqualified.json"), report);
        return report;
    }

    static Dictionary<string, object> SaveCopy(IModelDoc2 doc, string path)
    {
        doc.ClearSelection2(true);
        var previous = doc.GetPathName();
        int errors = 0, warnings = 0;
        int options = (int)(swSaveAsOptions_e.swSaveAsOptions_Silent | swSaveAsOptions_e.swSaveAsOptions_Copy);
        bool saved = doc.Extension.SaveAs3(path, 0, options, null, null, ref errors, ref warnings);
        Check(doc.GetPathName() == previous, "Saving a copy unexpectedly changed the active authoring document");
        return Row("success", saved, "errors", errors, "warnings", warnings, "native_options", options);
    }

    static Dictionary<string, object> Save(IModelDoc2 doc, string directory, string id, int count,
        Dictionary<string, object> edge, Dictionary<string, object> process, double length, double angle, double radius)
    {
        var row = Observe(doc, count);
        if (edge != null)
            row.Add("flange", ReadEdge(doc, (string)edge["profile_dimension"], (string)edge["source_edge"], length, angle, radius));
        Check(!String.IsNullOrEmpty(id) && !Path.IsPathRooted(id) && id == Path.GetFileName(id)
            && id != "." && id != ".." && id.IndexOfAny(Path.GetInvalidFileNameChars()) < 0,
            "Capture ID must be a plain file name");
        var path = Path.Combine(directory, id + ".SLDPRT");
        Check(!File.Exists(path), "Refusing to overwrite an existing native archive");
        var save = SaveCopy(doc, path);
        Check((bool)save["success"] && (int)save["errors"] == 0 && (int)save["warnings"] == 0,
            "Native SaveAs copy failed: " + id + " " + Json.Serialize(save));
        var archive = Archive(path);
        row.Add("save_as", save);
        row.Add("archive", archive);
        WriteCheckpoint(Path.Combine(directory, id + ".saved.json"), Row("id", id, "native_process", process,
            "edge_authoring", edge, "observation", row));
        return row;
    }

    public static string Author(string executable, string specification, string id, string directory)
    {
        var recipe = Object(Json.DeserializeObject(specification));
        var choices = Items(recipe["cases"]).Select(Object).ToArray();
        var control = choices.Single(item => (string)item["id"] == id);
        var definitions = Object(recipe["bodies"]);
        var ids = Items(control["bodies"]).Cast<string>().ToArray();
        return SolidWorksScopeControl.RunOwnedPhase(executable, (app, process) =>
        {
            app.UserControlBackground = true;
            Check(app.UserControlBackground, "The owned authoring session did not retain background lifetime control");
            var template = app.GetDocumentTemplate((int)swDocumentTypes_e.swDocPART, "", 0, 0, 0);
            Check(File.Exists(template), "Missing the native part template");
            var templateArchive = Archive(template);
            return WithDocument(app, app.NewDocument(template, 0, 0, 0) as IModelDoc2, null, doc =>
            {
                var discoveryDirectory = control.ContainsKey("holdout") ? null : directory;
                var thicknesses = ids.Select(body => Length(Object(definitions[body]), "thickness_mm")).Distinct().ToArray();
                Check(thicknesses.Length == 1, "One measured offset datum supports only the declared equal-thickness contrasts");
                Dictionary<string, object> datumEvidence;
                var datum = CreateThicknessDatum(app, doc, thicknesses[0], out datumEvidence);
                var arguments = ids.Select(body => AddBase(app, doc, body, Object(definitions[body]), datum, id, discoveryDirectory)).ToArray();
                Check(Bodies(doc).Length == ids.Length, "Disjoint base-flange controls did not retain the authored body membership");
                var folder = Features(doc).FirstOrDefault(feature => feature.GetTypeName2() == "SolidBodyFolder");
                var bodyFolder = folder == null ? null : folder.GetSpecificFeature2() as IBodyFolder;
                Check(bodyFolder != null, "Native solid body folder is missing");
                bodyFolder.UpdateCutList();
                Dictionary<string, object> edge = null;
                double length = 0, angle = 0, radius = 0;
                var saves = new List<object>();
                Dictionary<string, object> flange = null;
                object flangeControl;
                if (control.TryGetValue("flange", out flangeControl))
                {
                    flange = Object(flangeControl);
                    var body = Object(definitions[(string)flange["body"]]);
                    edge = AddEdge(doc, body, flange);
                    length = Length(flange, "length_mm");
                    angle = Number(flange["angle_deg"]) * Math.PI / 180;
                    radius = Length(body, "radius_mm");
                    bodyFolder.UpdateCutList();
                }
                var original = Save(doc, directory, id, ids.Length, edge, process, length, angle, radius);
                saves.Add(original);
                if (edge != null && flange != null && flange.ContainsKey("edit_mm"))
                {
                    var dimension = (string)edge["profile_dimension"];
                    var editedLength = Length(flange, "edit_mm");
                    EditLength(doc, dimension, editedLength);
                    var edited = Save(doc, directory, id + "-edited", ids.Length, edge, process, editedLength, angle, radius);
                    Check(TotalVolume(edited) > TotalVolume(original) + 1e-12, "The length edit did not increase native volume");
                    saves.Add(edited);
                    EditLength(doc, dimension, length);
                    var restored = Save(doc, directory, id + "-restored", ids.Length, edge, process, length, angle, radius);
                    Check(Near(TotalVolume(restored), TotalVolume(original), 1e-12), "The length restoration did not restore native volume");
                    saves.Add(restored);
                }
                return Row("id", id, "recipe", control, "native_process", process, "template", templateArchive,
                    "support_feature", Row("name", datum.Name, "type", datum.GetTypeName2(),
                        "persist_reference", Identity(doc, datum), "definition", datumEvidence),
                    "base_authoring", arguments, "edge_authoring", edge, "saves", saves.ToArray());
            });
        }, true);
    }

    public static string Measure(string executable, string path, string expectedHash, int bodies,
        string identity, string dimensionName, string sourceEdge, double length, double angle, double radius)
    {
        var before = Archive(path);
        Check(String.Equals((string)before["sha256"], expectedHash, StringComparison.Ordinal), "Input archive SHA-256 differs from its receipt");
        return SolidWorksScopeControl.RunOwnedPhase(executable, (app, process) =>
        {
            app.UserControlBackground = true;
            Check(app.UserControlBackground, "The owned readback session did not retain background lifetime control");
            int partType = (int)swDocumentTypes_e.swDocPART;
            app.DocumentVisible(false, partType);
            try
            {
                int errors, warnings;
                var part = OpenPart(app, path, out errors, out warnings);
                var row = WithDocument(app, part, path, doc =>
                {
                    Check(doc.IsOpenedReadOnly() && errors == 0 &&
                        (warnings & ~(int)swFileLoadWarning_e.swFileLoadWarning_ReadOnly) == 0 &&
                        String.Equals(doc.GetPathName(), path, StringComparison.OrdinalIgnoreCase),
                        "Exact archive did not open cleanly and read-only, errors=" + errors + " warnings=" + warnings);
                    var observed = Observe(doc, bodies);
                    if (!String.IsNullOrEmpty(sourceEdge))
                        observed.Add("flange", ReadEdge(doc, dimensionName, sourceEdge, length, angle, radius));
                    return Row("id", identity, "native_process", process, "archive", before, "open_errors", errors,
                        "open_warnings", warnings, "read_only", true, "observation", observed);
                });
                var after = Archive(path);
                Check((string)before["sha256"] == (string)after["sha256"], "The read-only native verification changed the input file");
                return row;
            }
            finally { app.DocumentVisible(true, partType); }
        }, true);
    }
}
