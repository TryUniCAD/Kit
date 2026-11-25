using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using System.Web.Script.Serialization;
using SolidWorks.Interop.sldworks;

public sealed partial class SolidWorksCapture
{
    [ThreadStatic] internal static bool RoutineReadback;
    static readonly JavaScriptSerializer Json = new JavaScriptSerializer { MaxJsonLength = int.MaxValue };
    static readonly UTF8Encoding Utf8 = new UTF8Encoding(false);
    readonly ISldWorks app;
    readonly IMathUtility math;
    readonly string repo, output, template;
    readonly Dictionary<string, object>[] recipes;
    readonly string spec;

    SolidWorksCapture(string repo, string output)
        : this((ISldWorks)Activator.CreateInstance(Type.GetTypeFromProgID("SldWorks.Application")), repo, output) { }

    SolidWorksCapture(ISldWorks application, string repo, string output)
    {
        this.app = application;
        this.repo = repo;
        this.output = output;
        math = (IMathUtility)app.GetMathUtility();
        template = app.GetDocumentTemplate(1, "", 0, 0, 0);
        spec = Path.Combine(repo, "re", "automation", "PairSpecs.json");
        var root = Json.Deserialize<Dictionary<string, object>>(File.ReadAllText(spec));
        recipes = Array((object)root["recipes"]).Cast<Dictionary<string, object>>().ToArray();
        Console.WriteLine("SOLIDWORKS " + app.RevisionNumber() + " PID " + app.GetProcessID());
    }

    static Dictionary<string, object> Row(params object[] values)
    {
        var row = new Dictionary<string, object>();
        for (int i = 0; i < values.Length; i += 2) row.Add((string)values[i], values[i+1]);
        return row;
    }

    static object[] Array(object value)
    {
        return value as object[] ?? (value as System.Collections.IEnumerable ?? new object[0]).Cast<object>().ToArray();
    }

    static double[] Vector(double x, double y, double z) { return new[] { x, y, z }; }
    static double[] V(ISketchPoint p) { return Vector(p.X, p.Y, p.Z); }
    static double[] Scale(double[] v, double factor) { return v.Select(x => x * factor).ToArray(); }
    static double[] World(string basis, double u, double v, double n)
    {
        if (basis == "YZ") return Vector(n,u,v);
        if (basis == "XZ") return Vector(u,-n,v);
        return Vector(u,v,n);
    }
    static void Check(bool ok, string failure) { if (!ok) throw new InvalidOperationException(failure); }
    static string Hash(string path)
    {
        using (var sha = SHA256.Create())
        using (var stream = new FileStream(path,FileMode.Open,FileAccess.Read,FileShare.ReadWrite | FileShare.Delete))
            return BitConverter.ToString(sha.ComputeHash(stream)).Replace("-", "").ToLowerInvariant();
    }
    static void Write(string path, object row) { File.WriteAllText(path, Json.Serialize(row) + "\n", Utf8); }
    double[] Transform(double[] xyz, MathTransform transform)
    {
        return (double[])((IMathPoint)math.CreatePoint(xyz)).IMultiplyTransform(transform).ArrayData;
    }
    static void Select(ISketchSegment seg, bool append = false)
    {
        Check(seg.Select4(append, null), "Select sketch segment");
    }
    static void Select(ISketchPoint point, bool append = false)
    {
        Check(point.Select4(append, null), "Select sketch point");
    }
    static void Origin(IModelDoc2 doc, bool append = false)
    {
        Check(doc.Extension.SelectByID2("Point1@Origin","EXTSKETCHPOINT",0,0,0,append,0,null,0), "Select origin");
    }
    static void Units(IModelDoc2 doc, int mode)
    {
        Check(doc.Extension.SetUserPreferenceInteger(263,0,mode), "Set document units");
        Check(doc.Extension.GetUserPreferenceInteger(263,0) == mode, "Verify document units");
    }
    static IDimension SetName(IDisplayDimension display, string name, double value)
    {
        Check(display != null, "Create dimension " + name);
        var dimension = (IDimension)display.GetDimension2(0);
        dimension.Name = name;
        Check(dimension.Name == name, "Rename dimension " + name + ": " + dimension.Name);
        Check(Math.Abs(dimension.SystemValue - value) < 1e-8, "Dimension " + name + " measured " + dimension.SystemValue + " expected " + value);
        return dimension;
    }
    static IDimension EdgeDimension(IModelDoc2 doc, ISketchSegment edge, string name, double value)
    {
        doc.ClearSelection2(true);
        Select(edge);
        return SetName(doc.IAddDimension2(.075,.075,.075),name,value);
    }
    IDimension OriginDimension(IModelDoc2 doc, ISketch sketch, ISketchPoint p, string basis, int axis, string name, double value)
    {
        doc.ClearSelection2(true);
        Origin(doc);
        Select(p,true);
        var worldDir = axis == 0 ? World(basis,1,0,0) : World(basis,0,1,0);
        var transform = sketch.ModelToSketchTransform;
        var localOrigin = Transform(Vector(0,0,0),transform);
        var localUnit = Transform(worldDir,transform);
        var display = Math.Abs(localUnit[0] - localOrigin[0]) > .5
            ? doc.IAddHorizontalDimension2(.072,.073,.074)
            : doc.IAddVerticalDimension2(.071,.073,.075);
        return SetName(display,name,value);
    }
    static IDimension FeatureDimension(IFeature feature, string name, double value)
    {
        for (object item = feature.GetFirstDisplayDimension(); item != null; item = feature.GetNextDisplayDimension(item))
        {
            var display = (IDisplayDimension)item;
            var d = (IDimension)display.GetDimension2(0);
            if (d != null && Math.Abs(d.SystemValue - value) < 1e-8) return SetName(display,name,value);
        }
        throw new InvalidOperationException("No " + name + " dimension on " + feature.Name);
    }
    ISketch BeginSketch(IModelDoc2 doc, string basis, IEntity face)
    {
        doc.ClearSelection2(true);
        if (face != null) Check(face.Select4(false,null), "Select parent top face");
        else
        {
            var plane = basis == "YZ" ? "Right Plane" : basis == "XZ" ? "Top Plane" : "Front Plane";
            Check(doc.Extension.SelectByID2(plane,"PLANE",0,0,0,false,0,null,0), "Select " + plane);
        }
        doc.SketchManager.InsertSketch(true);
        var sketch = (ISketch)doc.SketchManager.ActiveSketch;
        Check(sketch != null, "Enter sketch");
        return sketch;
    }
    static IFeature EndSketch(IModelDoc2 doc, ISketch sketch, string name)
    {
        int status = sketch.GetConstrainedStatus();
        Check(status == 3, name + " sketch constraint status " + status);
        doc.ClearSelection2(true);
        doc.SketchManager.InsertSketch(true);
        var feature = (IFeature)sketch;
        feature.Name = name;
        return feature;
    }
    ISketchSegment[] Rectangle(IModelDoc2 doc, ISketch sketch, string basis, double a, double b, double c, double d, double n)
    {
        var transform = sketch.ModelToSketchTransform;
        var start = Transform(World(basis,a,b,n),transform);
        var end = Transform(World(basis,c,d,n),transform);
        var segments = Array(doc.SketchManager.CreateCornerRectangle(start[0],start[1],0,end[0],end[1],0)).Cast<ISketchSegment>().ToArray();
        Check(segments.Length == 4, "Create four rectangle edges");
        return segments;
    }
    ISketchPoint Corner(ISketch sketch, string basis, double u, double v, double n)
    {
        var local = Transform(World(basis,u,v,n),sketch.ModelToSketchTransform);
        return Array(sketch.GetSketchPoints2()).Cast<ISketchPoint>().Single(p => Math.Abs(p.X-local[0]) < 1e-8 && Math.Abs(p.Y-local[1]) < 1e-8);
    }
    ISketchSegment Edge(ISketch sketch, ISketchSegment[] edges, string basis, int constantAxis, double value)
    {
        var inverse = sketch.ModelToSketchTransform.IInverse();
        var axis = basis == "YZ" ? constantAxis+1 : basis == "XZ" && constantAxis == 1 ? 2 : constantAxis;
        return edges.Single(seg =>
        {
            var line = (ISketchLine)seg;
            return Math.Abs(Transform(V(line.IGetStartPoint2()),inverse)[axis]-value) < 1e-8
                && Math.Abs(Transform(V(line.IGetEndPoint2()),inverse)[axis]-value) < 1e-8;
        });
    }
    static IFeature Extrusion(IModelDoc2 doc, IFeature sketch, string name, bool reverse, double depth, bool cut, bool through)
    {
        doc.ClearSelection2(true);
        Check(sketch.Select2(false,0), "Select " + sketch.Name);
        var manager = doc.FeatureManager;
        var feature = cut
            ? manager.FeatureCut4(true,false,reverse,through?1:0,0,depth,0,false,false,false,false,0,0,false,false,false,false,false,true,true,false,false,false,0,0,false,false)
            : manager.FeatureExtrusion2(true,false,reverse,0,0,depth,0,false,false,false,false,0,0,false,false,false,false,false,true,true,0,0,false);
        Check(feature != null, "Create " + name);
        feature.Name = name;
        if (!through) FeatureDimension(feature,cut?"cut_depth_mm":"depth_mm",depth);
        return feature;
    }

    IModelDoc2 Build(string id, string basis, bool reverse, bool through)
    {
        var doc = (IModelDoc2)app.INewDocument2(template,0,0,0);
        Check(doc != null,"New SOLIDWORKS part");
        try
        {
            Units(doc,5);
            var sketch = BeginSketch(doc,basis,null);
            if (id == "P02")
            {
                var circle = (ISketchSegment)doc.SketchManager.CreateCircleByRadius(0,0,0,ConfiguredValue(id,"diameter_mm",.010)/2);
                Check(circle != null,"Create origin circle");
                if (sketch.RelationManager.GetRelationsCount(0) == 0)
                {
                    doc.ClearSelection2(true);
                    Origin(doc);
                    Select(((ISketchArc)circle).IGetCenterPoint2(),true);
                    doc.SketchAddConstraints("sgCOINCIDENT");
                }
                doc.ClearSelection2(true);
                Select(circle);
                SetName(doc.IAddDiameterDimension2(.014,.014,.014),"diameter_mm",ConfiguredValue(id,"diameter_mm",.010));
                EndSketch(doc,sketch,"CircleSketch");
            }
            else if (id == "P05")
            {
                double innerRadius=ConfiguredValue(id,"inner_radius_mm",.002);
                double outerRadius=ConfiguredValue(id,"outer_radius_mm",.006);
                double height=ConfiguredValue(id,"height_mm",.012);
                var outline = Rectangle(doc,sketch,basis,innerRadius,0,outerRadius,height,0);
                var inner = Corner(sketch,basis,innerRadius,0,0);
                var outer = Corner(sketch,basis,outerRadius,0,0);
                doc.ClearSelection2(true);
                Origin(doc);
                Select(inner,true);
                doc.SketchAddConstraints("sgHORIZPOINTS");
                OriginDimension(doc,sketch,inner,basis,0,"inner_radius_mm",innerRadius);
                OriginDimension(doc,sketch,outer,basis,0,"outer_radius_mm",outerRadius);
                EdgeDimension(doc,Edge(sketch,outline,basis,0,innerRadius),"height_mm",height);
                var end = Transform(World(basis,0,.02,0),sketch.ModelToSketchTransform);
                var manager = doc.SketchManager;
                manager.AddToDB = true;
                ISketchSegment axis;
                try { axis = (ISketchSegment)manager.CreateCenterLine(0,0,0,end[0],end[1],0); }
                finally { manager.AddToDB = false; }
                Check(axis != null,"Create world Z construction axis");
                doc.ClearSelection2(true);
                Select(axis);
                doc.SketchAddConstraints("sgFIXED");
                var profile = EndSketch(doc,sketch,"AnnulusProfile");
                Check(profile.Select2(false,0),"Select axis-bound profile");
                double angle=ConfiguredValue(id,"angle_deg",2*Math.PI);
                var feature = doc.FeatureManager.FeatureRevolve2(true,true,false,false,false,false,0,0,angle,0,false,false,0,0,0,0,0,false,true,true);
                Check(feature != null,"Create full revolution");
                feature.Name = "Revolution";
                FeatureDimension(feature,"angle_deg",angle);
            }
            else
            {
                double width=ConfiguredValue(id,"width_mm",.04);
                double height=ConfiguredValue(id,"height_mm",.02);
                double depth=ConfiguredValue(id,"depth_mm",.01);
                var edges = Rectangle(doc,sketch,basis,0,0,width,height,0);
                EdgeDimension(doc,Edge(sketch,edges,basis,1,0),"width_mm",width);
                EdgeDimension(doc,Edge(sketch,edges,basis,0,0),"height_mm",height);
                var profile = EndSketch(doc,sketch,"RectangleSketch");
                if (id != "P01")
                {
                    Extrusion(doc,profile,"BlindBoss",reverse,depth,false,false);
                    if (id == "P04")
                    {
                        Check(doc.ForceRebuild3(false),"Rebuild parent boss");
                        var normal = World(basis,0,0,1);
                        var body = Array(((IPartDoc)doc).GetBodies2(0,false)).Cast<IBody2>().Single();
                        var face = Array(body.GetFaces()).Cast<IFace2>().Single(f =>
                            ((double[])f.Normal).Zip(normal,(a,b)=>Math.Abs(a-b)).Sum() < 1e-8);
                        var cut = BeginSketch(doc,basis,(IEntity)face);
                        double cutWidth=ConfiguredValue(id,"cut_width_mm",.010);
                        double cutHeight=ConfiguredValue(id,"cut_height_mm",.008);
                        double cutLeft=configuredCase == null ? .015 : (width-cutWidth)/2;
                        double cutBottom=configuredCase == null ? .006 : (height-cutHeight)/2;
                        var edgesCut = Rectangle(doc,cut,basis,cutLeft,cutBottom,
                            configuredCase == null ? .025 : cutLeft+cutWidth,
                            configuredCase == null ? .014 : cutBottom+cutHeight,depth);
                        var corner = Corner(cut,basis,cutLeft,cutBottom,depth);
                        EdgeDimension(doc,Edge(cut,edgesCut,basis,1,cutBottom),"cut_width_mm",cutWidth);
                        EdgeDimension(doc,Edge(cut,edgesCut,basis,0,cutLeft),"cut_height_mm",cutHeight);
                        var du = OriginDimension(doc,cut,corner,basis,0,"cut_left_mm",cutLeft);
                        var dv = OriginDimension(doc,cut,corner,basis,1,"cut_bottom_mm",cutBottom);
                        var cutProfile = EndSketch(doc,cut,"CutSketch");
                        var equations = doc.GetEquationMgr();
                        SetEquation(equations,du,"width_mm@RectangleSketch","cut_width_mm@CutSketch");
                        SetEquation(equations,dv,"height_mm@RectangleSketch","cut_height_mm@CutSketch");
                        Extrusion(doc,cutProfile,through?"ThroughAllCut":"BlindCut",false,ConfiguredValue(id,"cut_depth_mm",.004),true,through);
                    }
                }
            }
            Rebuild(doc);
            return doc;
        }
        catch { Close(doc); throw; }
    }

    static void SetEquation(IEquationMgr manager, IDimension dimension, string parent, string width)
    {
        var equation = "\"" + dimension.Name + "@CutSketch\" = (\"" + parent + "\" - \"" + width + "\") / 2";
        Check(manager.Add2(-1,equation,true) >= 0,"Add " + equation);
    }
    static void Rebuild(IModelDoc2 doc) { Check(doc.ForceRebuild3(false),"Rebuild " + doc.GetTitle()); }
    void Close(IModelDoc2 doc) {
        string path=doc.GetPathName();
        app.CloseDoc(doc.GetTitle());
        if(RoutineReadback) {
            Check(app.GetDocumentCount()==0,"Routine document close retained an open document");
            Check(String.IsNullOrEmpty(path) || app.GetOpenDocumentByName(path)==null,
                "Routine document close retained the saved model in memory");
        }
    }
    IModelDoc2 Open(string path, out object status, bool readOnly = false)
    {
        string pin=Hash(path);
        int initialDocuments=app.GetDocumentCount();
        var attempts=new List<object>();
        var elapsed=System.Diagnostics.Stopwatch.StartNew();
        status=null;
        for(int attempt=1;attempt<=3;attempt++) {
            int errors=0,warnings=0;
            IModelDoc2 doc=null;
            var record=Row("attempt",attempt);
            var clock=System.Diagnostics.Stopwatch.StartNew();
            try {
                doc=app.OpenDoc6(path,1,readOnly ? 3 : 1,"",ref errors,ref warnings);
                Check(doc!=null && errors==0 && (warnings==0 || (readOnly && warnings==2)),
                    "Open "+path+": errors "+errors+", warnings "+warnings);
                Check(String.Equals(Path.GetFullPath(doc.GetPathName()),Path.GetFullPath(path),StringComparison.OrdinalIgnoreCase),
                    "Open returned a different document "+path);
                Check(Hash(path)==pin,"Open changed saved bytes "+path);
                status=Row("errors",errors,"warnings",warnings);
                record["opened"]=true;
                return doc;
            } catch(Exception failure) {
                record["opened"]=false;
                record["failure"]=failure.ToString();
                if(doc!=null) {
                    Check(String.Equals(Path.GetFullPath(doc.GetPathName()),Path.GetFullPath(path),StringComparison.OrdinalIgnoreCase),
                        "Refuse cleanup of a different document "+path);
                    Close(doc);
                }
                Check(Hash(path)==pin && app.GetDocumentCount()==initialDocuments,
                    "Cannot safely retry open after document or saved bytes changed "+path);
                if(attempt==3) throw;
            } finally {
                record["errors"]=errors;
                record["warnings"]=warnings;
                record["seconds"]=clock.Elapsed.TotalSeconds;
                record["total_seconds"]=elapsed.Elapsed.TotalSeconds;
                attempts.Add(record);
                Directory.CreateDirectory(output);
                File.AppendAllText(Path.Combine(output,"open-attempts.jsonl"),
                    Json.Serialize(Row("file",Path.GetFullPath(path),"pid",app.GetProcessID(),"attempt",record))+"\n",Utf8);
            }
            System.Threading.Thread.Sleep(1000);
        }
        throw new InvalidOperationException("Open attempts exhausted "+path);
    }
    Dictionary<string,object> Save(IModelDoc2 doc, string path, bool copy)
    {
        Check(!File.Exists(path),"Capture file already exists " + path);
        int errors=0,warnings=0;
        bool ok = doc.Extension.SaveAs(path,0,copy?3:1,null,ref errors,ref warnings);
        Check(ok && errors == 0 && warnings == 0 && File.Exists(path),"Save " + path + ": errors " + errors + ", warnings " + warnings);
        Console.WriteLine("Saved " + Path.GetFileName(path));
        return Row("file",Path.GetFileName(path),"sha256",Hash(path),"size_bytes",new FileInfo(path).Length,"save_errors",errors,"save_warnings",warnings);
    }
    static List<IFeature> Features(IModelDoc2 doc)
    {
        var collected = new List<IFeature>();
        var seen = new HashSet<string>();
        for (var f = (IFeature)doc.FirstFeature(); f != null; f = (IFeature)f.GetNextFeature())
            Collect(f,collected,seen);
        return collected;
    }
    static void Collect(IFeature f, List<IFeature> collected, HashSet<string> seen)
    {
        if (!seen.Add(f.Name + "/" + f.GetTypeName2())) return;
        collected.Add(f);
        for (var c = (IFeature)f.GetFirstSubFeature(); c != null; c = (IFeature)c.GetNextSubFeature()) Collect(c,collected,seen);
    }
    static IEnumerable<IDimension> Dimensions(IFeature f, string name = null)
    {
        for (object d = f.GetFirstDisplayDimension(); d != null; d = f.GetNextDisplayDimension(d))
        {
            var dim = (IDimension)((IDisplayDimension)d).GetDimension2(0);
            if (dim == null) continue;
            if (name == null) name = f.Name;
            if (dim.FullName.Split('@')[1] == name) yield return dim;
        }
    }
    static object DescribeEntity(object entity)
    {
        var segment=entity as ISketchSegment;
        var point=entity as ISketchPoint;
        if (point != null) return Row("point_local_mm",Scale(V(point),1000),"id",point.GetID());
        if (segment != null) return Row("segment_type",segment.GetType(),"id",segment.GetID());
        return Row("external_entity_type",(entity as IEntity) == null ? (object)null : ((IEntity)entity).GetType());
    }
    object DescribeSketch(IModelDoc2 doc, IFeature feature, ISketch sketch)
    {
        int supportType=0;
        var support = sketch.GetReferenceEntity(ref supportType);
        var transform = sketch.ModelToSketchTransform;
        var inverse = transform.IInverse();
        var entities = new List<object>();
        foreach (var seg in Array(sketch.GetSketchSegments()).Cast<ISketchSegment>())
        {
            var row = Row("type",seg.GetType(),"id",seg.GetID(),"construction",seg.ConstructionGeometry,"length_mm",seg.GetLength()*1000);
            var line=seg as ISketchLine;
            var arc=seg as ISketchArc;
            if (line != null)
            {
                row["start_world_mm"] = Scale(Transform(V(line.IGetStartPoint2()),inverse),1000);
                row["end_world_mm"] = Scale(Transform(V(line.IGetEndPoint2()),inverse),1000);
            }
            if (arc != null)
            {
                row["center_world_mm"] = Scale(Transform(V(arc.IGetCenterPoint2()),inverse),1000);
                row["radius_mm"] = arc.GetRadius()*1000;
            }
            entities.Add(row);
        }
        var relations = Array(sketch.RelationManager.GetRelations(0)).Cast<ISketchRelation>().Select(rel =>
            Row("type",rel.GetRelationType(),"entity_types",rel.GetEntitiesType(),"entities",Array(rel.GetEntities()).Select(DescribeEntity).ToArray())).ToArray();
        doc.ClearSelection2(true);
        feature.Select2(false,0);
        var section = (double[])doc.Extension.GetSectionProperties2(new object[]{(IFeature)sketch});
        doc.ClearSelection2(true);
        bool measured = section != null && section.Length > 4 && section[0] == 0;
        string name = feature.Name;
        Check(measured,"Section properties for " + name + ": " + (section==null?"null":section[0].ToString()));
        int constraintStatus = sketch.GetConstrainedStatus();
        return Row("name",name,"support_type",supportType,"support_name",(support as IFeature)==null?null:((IFeature)support).Name,
            "model_to_sketch_transform",transform.ArrayData,"entities",entities,
            "relations",relations,"constraint_status",constraintStatus,"fully_defined",constraintStatus==3,
            "region_count",sketch.GetSketchRegionCount(),"section_area_mm2",section[1]*1e6,"section_center_world_mm",Scale(section.Skip(2).Take(3).ToArray(),1000));
    }
    Dictionary<string,object> Measure(IModelDoc2 doc, string label, bool scanSketches)
    {
        int bodies=Array(((IPartDoc)doc).GetBodies2(0,false)).Length;
        var extension = doc.Extension;
        var row=Row("label",label,"units_code",extension.GetUserPreferenceInteger(263,0),
            "configuration",doc.IGetActiveConfiguration().Name,"body_count",bodies,"volume_mm3",null,"center_of_mass_mm",null);
        if (bodies > 0)
        {
            var mass = (IMassProperty2)extension.CreateMassProperty2();
            Check(mass != null,"Create mass properties");
            mass.UseSystemUnits=true;
            Check(mass.Recalculate(),"Recalculate mass properties");
            row["volume_mm3"]=mass.Volume*1e9;
            row["center_of_mass_mm"]=Scale((double[])mass.CenterOfMass,1000);
        }
        if (!scanSketches) return row;
        var tree=new List<object>();
        var sketches=new List<object>();
        foreach(var f in Features(doc))
        {
            string name = f.Name;
            string type = f.GetTypeName2();
            bool warning=false;
            int code=f.GetErrorCode2(out warning);
            Check(code == 0,"Feature " + name + " error/warning code " + code);
            var dimensions=Dimensions(f,name).Select(d=>Row("name",d.Name,"full_name",d.FullName,"driven_state",d.DrivenState,"system_value",d.SystemValue)).ToArray();
            var definition=f.GetDefinition();
            var ext=definition as IExtrudeFeatureData2;
            var revolve=definition as IRevolveFeatureData2;
            object operation=null;
            if (ext != null) operation=Row("end_condition",ext.GetEndCondition(true),"depth_m",ext.GetDepth(true),"reverse_direction",ext.ReverseDirection,"both_directions",ext.BothDirections);
            if (revolve != null) operation=Row("angle_rad",revolve.GetRevolutionAngle(true),"reverse_direction",revolve.ReverseDirection,"axis_type",revolve.GetAxisType());
            tree.Add(Row("name",name,"type",type,"suppressed",f.IsSuppressed(),"error_code",code,"warning",warning,"dimensions",dimensions,"operation",operation));
            if (type=="ProfileFeature") sketches.Add(DescribeSketch(doc,f,(ISketch)f.GetSpecificFeature2()));
        }
        var equations=doc.GetEquationMgr();
        row["feature_tree"]=tree;
        row["sketches"]=sketches;
        row["equations"]=Enumerable.Range(0,equations.GetCount()).Select(i=>equations.Equation[i]).ToArray();
        return row;
    }
    Dictionary<string,object> Control(string label)
    {
        if (app.GetDocumentCount() != 0)
            return ReadControl(label, false);

        // a stock part opened without a window avoids the final document close stall
        app.DocumentVisible(false, 1);
        try { return ReadControl(label, true); }
        finally { app.DocumentVisible(true, 1); }
    }
    Dictionary<string,object> ReadControl(string label, bool discard)
    {
        var path=Path.Combine(repo,"re","solidworks","examples",".SLDPRT","example.SLDPRT");
        object status;
        var doc=Open(path,out status,true);
        try
        {
            Rebuild(doc);
            var row=Measure(doc,label,false);
            Check((int)row["body_count"]>0 && (double)row["volume_mm3"]>0,"Healthy control " + label);
            row["native_sha256"]=Hash(path);
            row["open_status"]=status;
            Console.WriteLine("Control " + label + " volume " + row["volume_mm3"]);
            return row;
        }
        finally
        {
            // the sole read-only stock control can close without entering the save path
            if (discard && doc.IsOpenedReadOnly() && app.GetDocumentCount() == 1
                && string.Equals(doc.GetPathName(), path, StringComparison.OrdinalIgnoreCase))
            {
                app.QuitDoc(doc.GetTitle());
                Check(app.GetDocumentCount() == 0, "Read-only stock control did not close");
            }
            else
                Close(doc);
        }
    }
    static void Set(IModelDoc2 doc, string name, double value)
    {
        var d=Features(doc).SelectMany(feature=>Dimensions(feature)).Single(dim=>dim.Name==name);
        int status=d.SetSystemValue3(value,1,null);
        Check(status==0 && Math.Abs(d.SystemValue-value)<1e-8,"Set " + name + ": " + status+" value "+d.SystemValue);
        Rebuild(doc);
    }
    Dictionary<string,object> Reopen(string path)
    {
        object status;
        var doc=Open(path,out status);
        try
        {
            Rebuild(doc);
            var row=Measure(doc,"reopened and rebuilt",true);
            row["open_status"]=status;
            return row;
        }
        finally { Close(doc); }
    }
    static string Filename(string id, string suffix) { return id + "-solidworks-" + suffix + ".SLDPRT"; }
    string Basis(string id) { return configuredCase == null ? (id=="P05"?"XZ":"XY") : (string)configuredOptions["basis"]; }
    void First(Dictionary<string,object> recipe)
    {
        var id=(string)recipe["id"];
        var dir=Path.Combine(output,id);
        Directory.CreateDirectory(dir);
        MarkStage("healthy_control_before");
        var observations=Row("healthy_control_before",Control("before"));
        MarkStage("baseline_authoring");
        var doc=Build(id,Basis(id),configuredCase != null && (int)configuredOptions["direction"] == -1,
            configuredCase != null && (string)configuredOptions["termination"] == "through_all");
        try
        {
            observations["baseline"]=Measure(doc,"as built",true);
            var save=Save(doc,Path.Combine(dir,Filename(id,"baseline-a")),false);
            Write(Path.Combine(dir,"first.json"),Row("observations",observations,"first_save",save,"authoring_process_id",app.GetProcessID()));
        }
        finally { Close(doc); }
    }
    void Second(Dictionary<string,object> recipe)
    {
        var id=(string)recipe["id"];
        var dir=Path.Combine(output,id);
        var first=Json.Deserialize<Dictionary<string,object>>(File.ReadAllText(Path.Combine(dir,"first.json")));
        var observations=(Dictionary<string,object>)first["observations"];
        var saves=new List<Dictionary<string,object>> { (Dictionary<string,object>)first["first_save"] };
        var initial=(Dictionary<string,object>)recipe["driving_parameters"];
        var edits=new List<object>();
        var variants=new List<object>();
        string basis=Basis(id);
        Func<string,string> path=suffix=>Path.Combine(dir,Filename(id,suffix));
        object status;
        Check(RoutineReadback || Convert.ToInt32(first["authoring_process_id"])!=app.GetProcessID(),"Baseline repeat requires a fresh SOLIDWORKS process");
        Check(Hash(path("baseline-a"))==(string)saves[0]["sha256"],"Baseline A hash changed");
        MarkStage("baseline_reopen");
        var doc=Open(path("baseline-a"),out status);
        try
        {
            observations["fresh_reopen"]=Row("open_status",status,"measurements",Measure(doc,"baseline A as opened",true));
            Rebuild(doc);
            observations["unchanged_rebuild"]=Measure(doc,"baseline A after rebuild",true);
            saves.Add(Save(doc,path("baseline-b"),true));
            MarkStage("edit_generation");
            foreach(var edit in Array(recipe["independent_edits"]).Cast<Dictionary<string,object>>())
            {
                string name=(string)edit["parameter"];
                double multiplier=name=="angle_deg"?Math.PI/180:.001;
                var suffix="edit-"+name+"-"+edit["value"];
                Set(doc,name,Convert.ToDouble(edit["value"])*multiplier);
                var changed=Measure(doc,suffix,true);
                saves.Add(Save(doc,path(suffix),true));
                Set(doc,name,Convert.ToDouble(initial[name])*multiplier);
                edits.Add(Row("parameter",name,"edited",changed,"restored",Measure(doc,"restored "+name,true),"saved_file",Filename(id,suffix)));
            }
            Units(doc,3);
            variants.Add(Row("variant","units-inch","reading",Measure(doc,"inch display units",true)));
            saves.Add(Save(doc,path("units-inch"),true));
        }
        finally { Close(doc); }
        MarkStage("variant_generation");
        if (id != "P05") CaptureVariant(id,dir,"plane-yz","YZ",false,false,saves,variants);
        if (id == "P03") CaptureVariant(id,dir,"direction-negative",basis,true,false,saves,variants);
        if (id == "P04") CaptureVariant(id,dir,"termination-through-all",basis,false,true,saves,variants);
        observations["edits"]=edits;
        observations["variants"]=variants;
        var reopened=new Dictionary<string,object>();
        MarkStage("saved_file_verification");
        foreach(var save in saves)
        {
            var file=(string)save["file"];
            var saved=Path.Combine(dir,file);
            reopened[file]=Reopen(saved);
            Check(Hash(saved)==(string)save["sha256"],"Saved bytes changed during reopen " + file);
        }
        observations["reopened_files"]=reopened;
        MarkStage("healthy_control_after");
        observations["healthy_control_after"]=Control("after");
        MarkStage("receipt_publication");
        var measurements=Path.Combine(dir,"measurements.json");
        var binary=System.Diagnostics.Process.GetProcessById(app.GetProcessID()).MainModule.FileVersionInfo.FileVersion;
        Write(measurements,Row("recipe_id",id,"application","SOLIDWORKS 2026","exact_application_build",app.RevisionNumber(),"executable_file_version",binary,
            "specifications_sha256",Hash(spec),"authoring_origin","Independently authored in SOLIDWORKS from PairSpecs.json through the SOLIDWORKS API.",
            "world_basis",basis,"authoring_process_id",first["authoring_process_id"],"reopen_process_id",app.GetProcessID(),
            "observations",observations,"saves",saves,"errors",new object[0]));
        Write(Path.Combine(dir,"receipt.json"),Row("recipe_id",id,"measurements","measurements.json","measurement_receipt_sha256",Hash(measurements),"native_files",saves,"errors",0));
    }
    void CaptureVariant(string id, string dir, string suffix, string basis, bool reverse, bool through,
        List<Dictionary<string,object>> saves, List<object> variants)
    {
        var built=Build(id,basis,reverse,through);
        try
        {
            variants.Add(Row("variant",suffix,"reading",Measure(built,suffix,true)));
            saves.Add(Save(built,Path.Combine(dir,Filename(id,suffix)),false));
        }
        finally { Close(built); }
    }
    public static void Run(string repo, string output, string recipe, string phase)
    {
        var run=new SolidWorksCapture(repo,output);
        if (phase=="exit")
        {
            Check(run.app.GetDocumentCount()==0,"SOLIDWORKS contains open documents");
            Console.WriteLine("Ending empty SOLIDWORKS capture process " + run.app.GetProcessID());
            run.app.ExitApp();
            return;
        }
        bool preference=run.app.GetUserPreferenceToggle(10);
        run.app.SetUserPreferenceToggle(10,false);
        try
        {
            foreach(var row in run.recipes.Where(r=>recipe=="" || (string)r["id"]==recipe))
            {
                Console.WriteLine(phase + " " + row["id"]);
                if(phase=="first") run.First(row);
                else if(phase=="second") run.Second(row);
                else if(phase=="build")
                {
                    var doc=run.Build((string)row["id"],run.Basis((string)row["id"]),false,false);
                    try { Console.WriteLine(Json.Serialize(run.Measure(doc,"as built",true))); }
                    finally { run.Close(doc); }
                }
                else throw new ArgumentException("Unknown phase "+phase);
            }
        }
        finally { run.app.SetUserPreferenceToggle(10,preference); }
    }
}
