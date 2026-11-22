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
    IModelDoc2 BuildProgram(Dictionary<string,object> Program,string BasisName,bool Reverse)
    {
        var Document=(IModelDoc2)app.INewDocument2(template,0,0,0);
        Check(Document!=null,"Create typed recipe part");
        try {
            Units(Document,5);
            var Operation=MapValue(Program["operation"]);
            bool Revolving=TextValue(Operation,"kind")=="revolve";
            if(Program["seed"]!=null) ProgramSeed(Document,MapValue(Program["seed"]),Revolving?"XY":BasisName);
            var Profile=ProgramProfile(Document,MapValue(Program["profile"]),BasisName,"RecipeProfile",Revolving);
            if(Revolving) RevolveProgram(Document,Profile,Operation,Reverse);
            else ExtrudeProgram(Document,Profile,Operation,BasisName,Reverse);
            Rebuild(Document);
            return Document;
        } catch { Close(Document); throw; }
    }

    void ProgramSeed(IModelDoc2 Document,Dictionary<string,object> Seed,string BasisName)
    {
        string Kind=TextValue(Seed,"kind");
        var Profile=Row("support","plane","origin_mm",new[]{0,0,0});
        if(Kind=="block") {
            Profile["kind"]="rectangle";
            Profile["width_mm"]=Seed["width_mm"];
            Profile["height_mm"]=Seed["depth_mm"];
        } else {
            Check(Kind=="cylinder","Unsupported typed recipe seed");
            Profile["kind"]="circle";
            Profile["diameter_mm"]=Seed["diameter_mm"];
        }
        var Sketch=ProgramProfile(Document,Profile,BasisName,"SeedProfile",false);
        Extrusion(Document,Sketch,"SeedFeature",IsFrameFlip((ISketch)Sketch.GetSpecificFeature2(),BasisName),Millimetres(Seed,"height_mm"),false,false);
        Rebuild(Document);
    }

    void ExtrudeProgram(IModelDoc2 Document,IFeature Profile,Dictionary<string,object> Operation,string BasisName,bool Reverse)
    {
        var Start=MapValue(Operation["start"]);
        bool FrameFlip=IsFrameFlip((ISketch)Profile.GetSpecificFeature2(),BasisName);
        var End=MapValue(Operation["end"]);
        string EndKind=TextValue(End,"kind");
        Reverse=Reverse^(FrameFlip && EndKind!="midplane");
        int EndCode=EndKind=="midplane"?6:EndKind=="up_to_plane"?4:0;
        IFeature EndPlane=null;
        if(EndKind=="up_to_plane") {
            Document.ClearSelection2(true);
            string PlaneName=BasisName=="YZ"?"Right Plane":BasisName=="XZ"?"Top Plane":"Front Plane";
            Check(Document.Extension.SelectByID2(PlaneName,"PLANE",0,0,0,false,0,null,0),"Select end plane support");
            var SeedSketch=(ISketch)Features(Document).Single(Found=>Found.Name=="SeedProfile").GetSpecificFeature2();
            EndPlane=Document.FeatureManager.InsertRefPlane(8|(IsFrameFlip(SeedSketch,BasisName)?256:0),Millimetres(End,"target_z_mm"),0,0,0,0) as IFeature;
            Check(EndPlane!=null,"Create live extrusion end plane");
            EndPlane.Name="EndPlane";
            FeatureDimension(EndPlane,"target_z_mm",Millimetres(End,"target_z_mm"));
        }
        Document.ClearSelection2(true);
        Check(Profile.Select2(false,0),"Select typed extrusion profile");
        if(EndPlane!=null) Check(EndPlane.Select2(true,1),"Select live extrusion end reference");
        bool Single=EndKind!="two_direction", Merge=TextValue(Operation,"effect")=="join";
        int StartCode=TextValue(Start,"kind")=="offset"?3:0;
        double FirstDepth=Millimetres(End,"depth1_mm"), SecondDepth=Millimetres(End,"depth2_mm");
        double Offset=Millimetres(Start,"offset_mm");
        bool FlipOffset=Convert.ToBoolean(Start["reverse"])^FrameFlip;
        Check(TextValue(Operation,"effect")!="cut","Typed extrusion cuts require a separate supported operation");
        IFeature Feature;
        if(Operation["thin"]!=null) {
            var Thin=MapValue(Operation["thin"]);
            int ThinCode=TextValue(Thin,"side")=="midplane"?2:0;
            Feature=Document.FeatureManager.FeatureExtrusionThin2(Single,false,Reverse,EndCode,0,FirstDepth,SecondDepth,
                false,false,false,false,0,0,false,false,false,false,Merge,Millimetres(Thin,"thickness_mm"),0,0,ThinCode,0,false,0,true,true,StartCode,Offset,FlipOffset);
        } else Feature=Document.FeatureManager.FeatureExtrusion3(Single,false,Reverse,EndCode,0,FirstDepth,SecondDepth,
            false,false,false,false,0,0,false,false,false,false,Merge,true,true,StartCode,Offset,FlipOffset);
        Check(Feature!=null,"Create typed extrusion");
        Feature.Name=TextValue(Operation,"feature_name");
    }
}
