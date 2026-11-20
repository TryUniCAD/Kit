// SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
// SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
//
// This SPDX license identifier and copyright notice must not be
// removed, altered, or obscured. Doing so is a material breach of
// the PolyForm Strict License 1.0.0 and voids all licenses granted
// to you under it immediately and permanently.

using System;
using System.Linq;
using SolidWorks.Interop.sldworks;

public sealed partial class SolidWorksCapture
{
    double[] ProgramNormal(ISketch Sketch)
    {
        var Inverse=Sketch.ModelToSketchTransform.IInverse();
        var OriginValue=Transform(Vector(0,0,0),Inverse);
        var NormalValue=Transform(Vector(0,0,1),Inverse).Zip(OriginValue,(First,Second)=>First-Second).ToArray();
        double Length=Math.Sqrt(NormalValue.Sum(Value=>Value*Value));
        Check(Length>0,"Native sketch has no normal");
        return Scale(NormalValue,1/Length);
    }

    bool IsFrameFlip(ISketch Sketch,string BasisName)
    {
        double Alignment=ProgramNormal(Sketch).Zip(World(BasisName,0,0,1),(First,Second)=>First*Second).Sum();
        Check(Math.Abs(Math.Abs(Alignment)-1)<1e-8,"Native sketch normal differs from requested basis");
        return Alignment<0;
    }

    bool IsFrameFlip(IModelDoc2 Document)
    {
        var Profile=(ISketch)Features(Document).Single(Feature=>Feature.Name=="RecipeProfile").GetSpecificFeature2();
        int Kind=0;
        var Support=Profile.GetReferenceEntity(ref Kind) as IFeature;
        if(Support==null) Support=((ISketch)Features(Document).Single(Feature=>Feature.Name=="SeedProfile").GetSpecificFeature2()).GetReferenceEntity(ref Kind) as IFeature;
        Check(Support!=null && new[]{"Front Plane","Right Plane","Top Plane"}.Contains(Support.Name),"Native recipe lost its basis owner");
        return IsFrameFlip(Profile,Support.Name=="Top Plane"?"XZ":Support.Name=="Right Plane"?"YZ":"XY");
    }
}
