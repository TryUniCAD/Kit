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

public sealed partial class SolidWorksCapture
{
    bool IsProgram() { return configuredOptions != null && configuredOptions.ContainsKey("program"); }
    Dictionary<string,object> ProgramData() { return MapValue(configuredOptions["program"]); }
    static Dictionary<string,object> MapValue(object Value)
    {
        var Result=Value as Dictionary<string,object>;
        Check(Result!=null,"Expected typed recipe object");
        return Result;
    }
    static string TextValue(Dictionary<string,object> Value,string Name)
    {
        Check(Value.ContainsKey(Name) && Value[Name] is string,"Missing recipe text "+Name);
        return (string)Value[Name];
    }
    static double NumberValue(Dictionary<string,object> Value,string Name)
    {
        Check(Value.ContainsKey(Name) && (Value[Name] is int || Value[Name] is long || Value[Name] is double || Value[Name] is decimal),"Missing recipe number "+Name);
        double Number=Convert.ToDouble(Value[Name]);
        Check(!double.IsNaN(Number) && !double.IsInfinity(Number),"Nonfinite recipe number "+Name);
        return Number;
    }
    static double Millimetres(Dictionary<string,object> Value,string Name) { return NumberValue(Value,Name)*.001; }
    static double Radians(Dictionary<string,object> Value,string Name) { return NumberValue(Value,Name)*Math.PI/180; }
    static void CheckProgram(Dictionary<string,object> Program)
    {
        Check(Convert.ToInt32(Program["schema"])==1,"Unsupported recipe program schema");
        string Pin=TextValue(Program,"recipe_sha256");
        Check(Pin.Length==64 && Pin.All(Symbol=>"0123456789abcdef".Contains(Symbol)),"Invalid written recipe pin");
        var Profile=MapValue(Program["profile"]);
        string Kind=TextValue(Profile,"kind"), Support=TextValue(Profile,"support");
        Check(new[]{"rectangle","radial_rectangle","open_line","circle"}.Contains(Kind),"Unsupported native profile");
        Check(Support=="plane" || Support=="seed_top_face","Unsupported native support");
        Check(Array(Profile["origin_mm"]).Length==3,"Invalid native profile origin");
        var Operation=MapValue(Program["operation"]);
        string Method=TextValue(Operation,"kind"), Effect=TextValue(Operation,"effect");
        Check(Method=="extrude" || Method=="revolve","Unsupported native operation");
        Check(new[]{"new_body","join","cut"}.Contains(Effect),"Unsupported native effect");
        Check(Method!="extrude" || Effect!="cut","Typed extrusion cut is outside the supported program contract");
        Check(Effect=="new_body"?Program["seed"]==null:Program["seed"]!=null,"Native effect differs from its seed ownership");
        Check(TextValue(Operation,"feature_name")=="RecipeFeature","Unsupported native feature owner");
        if(Method=="extrude") {
            var Start=MapValue(Operation["start"]);
            var End=MapValue(Operation["end"]);
            Check(new[]{"sketch_plane","offset"}.Contains(TextValue(Start,"kind")),"Unsupported extrusion start");
            Check(new[]{"blind","two_direction","midplane","up_to_plane"}.Contains(TextValue(End,"kind")),"Unsupported extrusion end");
        }
        Check(Program.ContainsKey("bindings") && Program.ContainsKey("edits") && Program.ContainsKey("variants"),"Missing native recipe evidence plan");
    }
}
