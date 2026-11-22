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
using SolidWorks.Interop.sldworks;

public sealed partial class SolidWorksCapture
{
    IFeature ProgramProfile(IModelDoc2 Document, Dictionary<string,object> Profile, string BasisName, string OwnerName, bool Revolving)
    {
        IEntity Support=null;
        if(TextValue(Profile,"support")=="seed_top_face") {
            var Normal=World(BasisName,0,0,1);
            var Body=Array(((IPartDoc)Document).GetBodies2(0,false)).Cast<IBody2>().Single();
            Support=(IEntity)Array(Body.GetFaces()).Cast<IFace2>().Single(Face=> {
                var FaceNormal=Face.Normal as double[];
                return FaceNormal!=null && FaceNormal.Zip(Normal,(First,Second)=>Math.Abs(First-Second)).Sum()<1e-8;
            });
        }
        var Sketch=BeginSketch(Document,BasisName,Support);
        var OriginValues=Array(Profile["origin_mm"]).Select(Convert.ToDouble).Select(Value=>Value*.001).ToArray();
        string Shape=TextValue(Profile,"kind");
        if(Shape=="rectangle" || Shape=="radial_rectangle") {
            double Left=OriginValues[0], Bottom=OriginValues[1], Height=Millimetres(Profile,"height_mm");
            double Right=Left+(Shape=="rectangle"?Millimetres(Profile,"width_mm"):0);
            if(Shape=="radial_rectangle") { Left=Millimetres(Profile,"inner_radius_mm"); Right=Millimetres(Profile,"outer_radius_mm"); }
            var Edges=Rectangle(Document,Sketch,BasisName,Left,Bottom,Right,Bottom+Height,OriginValues[2]);
            if(Shape=="radial_rectangle") {
                var Inner=Corner(Sketch,BasisName,Left,Bottom,OriginValues[2]);
                Document.ClearSelection2(true); Origin(Document); Select(Inner,true);
                Document.SketchAddConstraints("sgHORIZPOINTS");
                OriginDimension(Document,Sketch,Inner,BasisName,0,"inner_radius_mm",Left);
                OriginDimension(Document,Sketch,Corner(Sketch,BasisName,Right,Bottom,OriginValues[2]),BasisName,0,"outer_radius_mm",Right);
            } else {
                Check(Math.Abs(Left)<1e-12 && Math.Abs(Bottom)<1e-12,"Rectangle profile requires the reviewed origin");
                EdgeDimension(Document,Edge(Sketch,Edges,BasisName,1,Bottom),"width_mm",Right-Left);
            }
            EdgeDimension(Document,Edge(Sketch,Edges,BasisName,0,Left),"height_mm",Height);
        } else if(Shape=="circle") {
            var Centre=Transform(World(BasisName,OriginValues[0],OriginValues[1],OriginValues[2]),Sketch.ModelToSketchTransform);
            double Diameter=Millimetres(Profile,"diameter_mm");
            var Circle=(ISketchSegment)Document.SketchManager.CreateCircleByRadius(Centre[0],Centre[1],0,Diameter/2);
            Check(Circle!=null,"Create recipe circle");
            var CentrePoint=((ISketchArc)Circle).IGetCenterPoint2();
            if(Math.Abs(OriginValues[0])+Math.Abs(OriginValues[1])<1e-12) {
                if(Sketch.RelationManager.GetRelationsCount(0)==0) {
                    Document.ClearSelection2(true); Origin(Document); Select(CentrePoint,true);
                    Document.SketchAddConstraints("sgCOINCIDENT");
                }
            } else {
                OriginDimension(Document,Sketch,CentrePoint,BasisName,0,"center_u_mm",OriginValues[0]);
                OriginDimension(Document,Sketch,CentrePoint,BasisName,1,"center_v_mm",OriginValues[1]);
            }
            Document.ClearSelection2(true); Select(Circle);
            SetName(Document.IAddDiameterDimension2(.071,.072,.073),"diameter_mm",Diameter);
        } else {
            double Length=Millimetres(Profile,"length_mm");
            bool AlongU=TextValue(Profile,"axis")=="u";
            var Start=Transform(World(BasisName,OriginValues[0],OriginValues[1],OriginValues[2]),Sketch.ModelToSketchTransform);
            var End=Transform(World(BasisName,OriginValues[0]+(AlongU?Length:0),OriginValues[1]+(AlongU?0:Length),OriginValues[2]),Sketch.ModelToSketchTransform);
            var Manager=Document.SketchManager;
            Manager.AddToDB=true;
            ISketchSegment Segment;
            try { Segment=(ISketchSegment)Manager.CreateLine(Start[0],Start[1],0,End[0],End[1],0); }
            finally { Manager.AddToDB=false; }
            Check(Segment!=null,"Create recipe open profile");
            Document.ClearSelection2(true); Select(Segment);
            Document.SketchAddConstraints(Math.Abs(End[0]-Start[0])>Math.Abs(End[1]-Start[1])?"sgHORIZONTAL":"sgVERTICAL");
            var StartPoint=((ISketchLine)Segment).IGetStartPoint2();
            Document.ClearSelection2(true); Origin(Document); Select(StartPoint,true);
            Document.SketchAddConstraints(Math.Abs(OriginValues[0])+Math.Abs(OriginValues[1])<1e-12?"sgCOINCIDENT":"sgHORIZPOINTS");
            if(Profile.ContainsKey("radius_mm")) OriginDimension(Document,Sketch,StartPoint,BasisName,0,"radius_mm",Millimetres(Profile,"radius_mm"));
            EdgeDimension(Document,Segment,"length_mm",Length);
        }
        if(Revolving) {
            var AxisEnd=Transform(World(BasisName,0,.03,0),Sketch.ModelToSketchTransform);
            var Manager=Document.SketchManager;
            Manager.AddToDB=true;
            ISketchSegment AxisLine;
            try { AxisLine=(ISketchSegment)Manager.CreateCenterLine(0,0,0,AxisEnd[0],AxisEnd[1],0); }
            finally { Manager.AddToDB=false; }
            Check(AxisLine!=null,"Create recipe revolution axis");
            Document.ClearSelection2(true); Select(AxisLine); Document.SketchAddConstraints("sgFIXED");
        }
        return EndSketch(Document,Sketch,OwnerName);
    }
}
