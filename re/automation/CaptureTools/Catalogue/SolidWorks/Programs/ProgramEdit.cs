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
    static double BindingValue(IFeature Feature,string FieldPath,bool FrameFlip=false)
    {
        string FieldName=FieldPath.Split('.').Last();
        var Definition=Feature.GetDefinition();
        var Extrude=Definition as IExtrudeFeatureData2;
        var Revolve=Definition as IRevolveFeatureData2;
        if(FieldName=="offset_mm" && Extrude!=null) return Extrude.FromOffsetDistance*1000*((Extrude.FromOffsetReverse^FrameFlip)?-1:1);
        if(FieldName=="depth1_mm" && Extrude!=null) return Extrude.GetDepth(true)*1000;
        if(FieldName=="depth2_mm" && Extrude!=null) return Extrude.GetDepth(false)*1000;
        if(FieldName=="angle1_deg" && Revolve!=null) return Revolve.GetRevolutionAngle(true)*180/Math.PI;
        if(FieldName=="angle2_deg" && Revolve!=null) return Revolve.GetRevolutionAngle(false)*180/Math.PI;
        if(FieldName=="thickness_mm") {
            if(Extrude!=null) return Extrude.GetWallThickness(true)*1000;
            if(Revolve!=null) return Revolve.GetWallThickness(true)*1000;
        }
        var Dimension=Dimensions(Feature).Single(Found=>Found.Name==FieldName);
        Check(Dimension.DrivenState==2,"Recipe binding must own a driving dimension");
        return Dimension.SystemValue*(FieldName.EndsWith("_deg")?180/Math.PI:1000);
    }

    void ProgramEdit(IModelDoc2 Document,Dictionary<string,object> Program,string Parameter,double Value)
    {
        var Binding=MapValue(MapValue(Program["bindings"])[Parameter]);
        bool FrameFlip=IsFrameFlip(Document);
        string OwnerName=TextValue(Binding,"owner"), FieldName=TextValue(Binding,"field").Split('.').Last();
        var Feature=Features(Document).Single(Found=>Found.Name==OwnerName);
        var Definition=Feature.GetDefinition();
        var Extrude=Definition as IExtrudeFeatureData2;
        var Revolve=Definition as IRevolveFeatureData2;
        bool Edited=false;
        if(Extrude!=null) {
            Check(Extrude.AccessSelections(Document,null),"Access editable extrusion owner");
            bool Access=true;
            try {
                if(FieldName=="offset_mm") { Extrude.FromOffsetDistance=Math.Abs(Value)*.001; Extrude.FromOffsetReverse=(Value<0)^FrameFlip; Edited=true; }
                if(FieldName=="depth1_mm" || FieldName=="depth2_mm") { Extrude.SetDepth(FieldName=="depth1_mm",Value*.001); Edited=true; }
                if(FieldName=="thickness_mm") { Extrude.SetWallThickness(true,Value*.001); Edited=true; }
                Check(Edited,"Unsupported extrusion edit binding");
                bool Modified=Feature.ModifyDefinition(Definition,Document,null);
                Access=false;
                Check(Modified,"Modify typed extrusion owner");
            } finally { if(Access) Extrude.ReleaseSelectionAccess(); }
        } else if(Revolve!=null) {
            Check(Revolve.AccessSelections(Document,null),"Access editable revolution owner");
            bool Access=true;
            try {
                if(FieldName=="angle1_deg" || FieldName=="angle2_deg") { Revolve.SetRevolutionAngle(FieldName=="angle1_deg",Value*Math.PI/180); Edited=true; }
                if(FieldName=="thickness_mm") { Revolve.SetWallThickness(true,Value*.001); Edited=true; }
                Check(Edited,"Unsupported revolution edit binding");
                bool Modified=Feature.ModifyDefinition(Definition,Document,null);
                Access=false;
                Check(Modified,"Modify typed revolution owner");
            } finally { if(Access) Revolve.ReleaseSelectionAccess(); }
        } else {
            var Dimension=Dimensions(Feature).Single(Found=>Found.Name==FieldName);
            Check(Dimension.DrivenState==2 && Dimension.SetSystemValue3(Value*(FieldName.EndsWith("_deg")?Math.PI/180:.001),1,null)==0,
                "Set owned recipe driving dimension");
        }
        Rebuild(Document);
        Check(Math.Abs(BindingValue(Feature,TextValue(Binding,"field"),FrameFlip)-Value)<1e-7,"Native edited property differs from requested value");
    }
}
