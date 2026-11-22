// SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
// SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
//
// This SPDX license identifier and copyright notice must not be
// removed, altered, or obscured. Doing so is a material breach of
// the PolyForm Strict License 1.0.0 and voids all licenses granted
// to you under it immediately and permanently.

using System;
using System.Collections.Generic;
using SolidWorks.Interop.sldworks;

public sealed partial class SolidWorksCapture
{
    void RevolveProgram(IModelDoc2 Document,IFeature Profile,Dictionary<string,object> Operation,bool Reverse)
    {
        var End=MapValue(Operation["end"]);
        string Ending=TextValue(End,"kind");
        var Thin=Operation["thin"]==null?null:MapValue(Operation["thin"]);
        Document.ClearSelection2(true);
        Check(Profile.Select2(false,0),"Select typed revolution profile");
        var Feature=Document.FeatureManager.FeatureRevolve2(Ending!="two_direction",true,Thin!=null,
            TextValue(Operation,"effect")=="cut",Reverse,false,Ending=="midplane"?6:0,0,
            Radians(Operation,"angle1_deg"),Radians(Operation,"angle2_deg"),false,false,0,0,
            Thin!=null && TextValue(Thin,"side")=="midplane"?2:0,
            Thin==null?0:Millimetres(Thin,"thickness_mm"),0,TextValue(Operation,"effect")=="join",true,true);
        Check(Feature!=null,"Create typed revolution");
        Feature.Name=TextValue(Operation,"feature_name");
    }
}
