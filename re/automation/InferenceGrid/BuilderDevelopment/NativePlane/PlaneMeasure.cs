// SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
// SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
//
// This SPDX license identifier and copyright notice must not be
// removed, altered, or obscured. Doing so is a material breach of
// the PolyForm Strict License 1.0.0 and voids all licenses granted
// to you under it immediately and permanently.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.InteropServices;
using SolidWorks.Interop.sldworks;

public sealed partial class SolidWorksCapture
{
    static object PlaneField(Dictionary<string,object> Errors,string Name,Func<object> Read)
    {
        try { return Read(); }
        catch(Exception Error) { Errors[Name]=Error.GetType().Name+": "+Error.Message; return null; }
    }

    static Dictionary<string,object> PlaneTransform(IFeature Feature)
    {
        var Plane=Feature.GetSpecificFeature2() as IRefPlane;
        Check(Plane!=null,"Observed feature has no native reference plane interface");
        MathTransform Transform=null;
        try {
            Transform=Plane.Transform;
            var Data=(double[])Transform.ArrayData;
            Check(Data.Length>=13,"Native reference plane transform is incomplete");
            var Normal=new[]{Data[6],Data[7],Data[8]};
            double Length=Math.Sqrt(Normal.Sum(Value=>Value*Value));
            Check(Length>0 && !double.IsNaN(Length) && !double.IsInfinity(Length),"Native reference plane normal is invalid");
            return Row("transform",Data,"origin_mm",new[]{Data[9]*1000,Data[10]*1000,Data[11]*1000},
                "normal_world",Normal.Select(Value=>Value/Length).ToArray());
        } finally { if(Transform!=null) Marshal.ReleaseComObject(Transform); }
    }

    Dictionary<string,object> PlaneDefinition(IModelDoc2 Document,IFeature Feature)
    {
        var Errors=new Dictionary<string,object>();
        var Result=Row("name",Feature.Name,"type",Feature.GetTypeName2(),"collection_errors",Errors);
        var Transform=PlaneField(Errors,"transform",()=>PlaneTransform(Feature)) as Dictionary<string,object>;
        if(Transform!=null) foreach(var Item in Transform) Result[Item.Key]=Item.Value;
        var Definition=Feature.GetDefinition() as IRefPlaneFeatureData;
        if(Definition==null) { Errors["definition"]="Native reference plane definition is unavailable"; return Result; }
        var Data=new Dictionary<string,object>();
        Result["definition"]=Data;
        Data["type"]=PlaneField(Errors,"type",()=>Definition.Type);
        Data["type2"]=PlaneField(Errors,"type2",()=>Definition.Type2);
        Data["distance_m"]=PlaneField(Errors,"distance_m",()=>Definition.Distance);
        Data["reverse_direction"]=PlaneField(Errors,"reverse_direction",()=>Definition.ReverseDirection);
        bool Access=false;
        try {
            Access=Definition.AccessSelections(Document,null);
            Check(Access,"Cannot access native plane references");
            Data["selection_count"]=Definition.GetSelectionsCount();
            var Selections=Array(Definition.Selections);
            Data["constraints"]=Enumerable.Range(0,Selections.Length).Select(Index=>
                PlaneField(Errors,"constraint_"+Index,()=>Definition.Constraint[Index])).ToArray();
            Data["references"]=Selections.Select(Selected=>{
                var Reference=Selected as IFeature;
                if(Reference==null) return Row("name",null,"type",Selected==null?null:Selected.GetType().Name);
                var ReferenceRow=Row("name",Reference.Name,"type",Reference.GetTypeName2());
                if(Reference.GetTypeName2()=="RefPlane") {
                    var Geometry=PlaneField(Errors,"reference_transform_"+Reference.Name,()=>PlaneTransform(Reference)) as Dictionary<string,object>;
                    if(Geometry!=null) foreach(var Item in Geometry) ReferenceRow[Item.Key]=Item.Value;
                }
                return ReferenceRow;
            }).ToArray();
        } catch(Exception Error) { Errors["references"]=Error.GetType().Name+": "+Error.Message; }
        finally { if(Access) Definition.ReleaseSelectionAccess(); }
        return Result;
    }

    Dictionary<string,object> MeasurePlane(IModelDoc2 Document,string Label)
    {
        var Reading=Measure(Document,Label,false);
        var Bodies=Array(((IPartDoc)Document).GetBodies2(0,false)).Cast<IBody2>().ToArray();
        Reading["surface_body_count"]=Array(((IPartDoc)Document).GetBodies2(1,false)).Length;
        var Bounds=new double[6];
        if(Bodies.Length>0) for(int Index=0;Index<6;Index++) {
            var Direction=new double[3]; Direction[Index%3]=Index<3?-1:1;
            var Values=new List<double>();
            foreach(var Body in Bodies) {
                double First=0,Second=0,Third=0;
                Check(Body.GetExtremePoint(Direction[0],Direction[1],Direction[2],out First,out Second,out Third),"Cannot collect native body extreme");
                Values.Add(new[]{First,Second,Third}[Index%3]*1000);
            }
            Bounds[Index]=Index<3?Values.Min():Values.Max();
        }
        Reading["bounds_mm"]=Bodies.Length==0?new double[0]:Bounds;
        var Tree=new List<object>(); var Sketches=new List<object>();
        foreach(var Feature in Features(Document)) {
            bool Warning=false; int Error=Feature.GetErrorCode2(out Warning);
            var Extrude=Feature.GetDefinition() as IExtrudeFeatureData2;
            Tree.Add(Row("name",Feature.Name,"type",Feature.GetTypeName2(),"suppressed",Feature.IsSuppressed(),
                "error_code",Error,"warning",Warning,"parents",Array(Feature.GetParents()).Cast<IFeature>().Select(Parent=>Parent.Name).ToArray(),
                "dimensions",Dimensions(Feature).Select(Dimension=>Row("name",Dimension.Name,"full_name",Dimension.FullName,
                    "driven_state",Dimension.DrivenState,"system_value",Dimension.SystemValue)).ToArray(),
                "operation",Extrude==null?null:Row("kind","extrude","end_condition",Extrude.GetEndCondition(true),
                    "depth_m",Extrude.GetDepth(true),"reverse_direction",Extrude.ReverseDirection,"both_directions",Extrude.BothDirections)));
            if(Feature.GetTypeName2()=="ProfileFeature") Sketches.Add(DescribeSketch(Document,Feature,(ISketch)Feature.GetSpecificFeature2()));
        }
        Reading["feature_tree"]=Tree; Reading["sketches"]=Sketches;
        var Target=Features(Document).SingleOrDefault(Feature=>Feature.Name=="RecipeFeature");
        Check(Target!=null,"Candidate did not retain its native feature");
        Reading["plane"]=PlaneDefinition(Document,Target);
        var Bindings=new Dictionary<string,object>();
        foreach(var Dimension in Dimensions(Target).Where(Dimension=>Dimension.Name=="offset_mm")) {
            Check(!Bindings.ContainsKey("offset_mm"),"Native offset dimension ownership is ambiguous");
            Bindings["offset_mm"]=Row("owner",Target.Name,"name",Dimension.Name,"full_name",Dimension.FullName,
                "driven_state",Dimension.DrivenState,"system_value",Dimension.SystemValue,"value_mm",Dimension.SystemValue*1000);
        }
        Reading["parameter_bindings"]=Bindings;
        return Reading;
    }
}
