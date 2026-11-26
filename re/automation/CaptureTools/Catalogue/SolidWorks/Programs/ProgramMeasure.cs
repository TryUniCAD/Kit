// SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
// SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
//
// This SPDX license identifier and copyright notice must not be
// removed, altered, or obscured. Doing so is a material breach of
// the PolyForm Strict License 1.0.0 and voids all licenses granted
// to you under it immediately and permanently.

using System;
using System.Collections.Generic;
using System.Linq;
using SolidWorks.Interop.sldworks;

public sealed partial class SolidWorksCapture
{
    Dictionary<string,object> ProgramMeasure(IModelDoc2 Document,string Label,Dictionary<string,object> Program)
    {
        var Reading=Measure(Document,Label,false);
        var Bodies=Array(((IPartDoc)Document).GetBodies2(0,false)).Cast<IBody2>().ToArray();
        Check(Bodies.Length==1,"Written solid recipe requires one solid body");
        Reading["surface_body_count"]=Array(((IPartDoc)Document).GetBodies2(1,false)).Length;
        var Bounds=new double[6];
        for(int Index=0;Index<6;Index++) {
            var Direction=new double[3]; Direction[Index%3]=Index<3?-1:1;
            double First=0,Second=0,Third=0;
            Check(Bodies[0].GetExtremePoint(Direction[0],Direction[1],Direction[2],out First,out Second,out Third),"Measure native body extreme");
            Bounds[Index]=new[]{First,Second,Third}[Index%3]*1000;
        }
        Reading["bounds_mm"]=Bounds;
        var Tree=new List<object>();
        var Sketches=new List<object>();
        foreach(var Feature in Features(Document)) {
            bool Warning=false;
            int Error=Feature.GetErrorCode2(out Warning);
            var Definition=Feature.GetDefinition();
            object Operation=null;
            if(Definition is IExtrudeFeatureData2) Operation=ExtrudeReading(Document,(IExtrudeFeatureData2)Definition);
            if(Definition is IRevolveFeatureData2) {
                var Revolve=(IRevolveFeatureData2)Definition;
                Operation=Row("kind","revolve","type",Revolve.Type,"angle1_rad",Revolve.GetRevolutionAngle(true),
                    "angle2_rad",Revolve.GetRevolutionAngle(false),"reverse_direction",Revolve.ReverseDirection,
                    "axis_type",Revolve.GetAxisType(),"thin",Revolve.IsThinFeature(),"thin_type",Revolve.ThinWallType,
                    "thickness1_m",Revolve.GetWallThickness(true),"thickness2_m",Revolve.GetWallThickness(false),"merge",Revolve.Merge);
            }
            var DimensionsRead=Dimensions(Feature).Select(Dimension=>Row("name",Dimension.Name,"full_name",Dimension.FullName,
                "driven_state",Dimension.DrivenState,"system_value",Dimension.SystemValue)).ToArray();
            Tree.Add(Row("name",Feature.Name,"type",Feature.GetTypeName2(),"suppressed",Feature.IsSuppressed(),
                "error_code",Error,"warning",Warning,"dimensions",DimensionsRead,"operation",Operation,
                "parents",Array(Feature.GetParents()).Cast<IFeature>().Select(Parent=>Parent.Name).ToArray()));
            if(Feature.GetTypeName2()=="ProfileFeature") {
                var Sketch=(ISketch)Feature.GetSpecificFeature2();
                var SketchRow=MapValue(Sketch.GetSketchRegionCount()>0?DescribeSketch(Document,Feature,Sketch):OpenSketchRead(Feature,Sketch));
                SketchRow["normal_world"]=ProgramNormal(Sketch);
                Sketches.Add(SketchRow);
            }
        }
        Reading["feature_tree"]=Tree;
        Reading["sketches"]=Sketches;
        var Bindings=new Dictionary<string,object>();
        foreach(var Binding in MapValue(Program["bindings"])) {
            var Contract=MapValue(Binding.Value);
            string OwnerName=TextValue(Contract,"owner"), FieldName=TextValue(Contract,"field");
            var Feature=Features(Document).Single(Found=>Found.Name==OwnerName);
            Bindings[Binding.Key]=Row("owner",OwnerName,"field",FieldName,"value",BindingValue(Feature,FieldName,IsFrameFlip(Document)));
        }
        Reading["parameter_bindings"]=Bindings;
        return Reading;
    }

    static object ExtrudeReading(IModelDoc2 Document,IExtrudeFeatureData2 Extrude)
    {
        object Reference=null;
        int ReferenceType=0;
        if(Extrude.GetEndCondition(true)==4) {
            Check(Extrude.AccessSelections(Document,null),"Access native extrusion references");
            try { Reference=Extrude.GetEndConditionReference(true,out ReferenceType); }
            finally { Extrude.ReleaseSelectionAccess(); }
        }
        var Feature=Reference as IFeature;
        return Row("kind","extrude","end1",Extrude.GetEndCondition(true),"end2",Extrude.GetEndCondition(false),
            "depth1_m",Extrude.GetDepth(true),"depth2_m",Extrude.GetDepth(false),"reverse_direction",Extrude.ReverseDirection,
            "both_directions",Extrude.BothDirections,"from_type",Extrude.FromType,"offset_m",Extrude.FromOffsetDistance,
            "offset_reverse",Extrude.FromOffsetReverse,"thin",Extrude.IsThinFeature(),"thin_type",Extrude.ThinWallType,
            "thickness1_m",Extrude.GetWallThickness(true),"thickness2_m",Extrude.GetWallThickness(false),"merge",Extrude.Merge,
            "end_reference_type",ReferenceType,"end_reference_name",Feature==null?null:Feature.Name);
    }
}
