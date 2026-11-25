// SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
// SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
//
// This SPDX license identifier and copyright notice must not be
// removed, altered, or obscured. Doing so is a material breach of
// the PolyForm Strict License 1.0.0 and voids all licenses granted
// to you under it immediately and permanently.

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using SolidWorks.Interop.sldworks;

public sealed partial class SolidWorksCapture
{
    Dictionary<string, object> configuredCase;
    Dictionary<string, object> configuredParams;
    Dictionary<string, object> configuredOptions;

    double ConfiguredValue(string recipe, string parameter, double fallback)
    {
        if (configuredCase == null || (string)configuredCase["recipe"] != recipe
            || !configuredParams.ContainsKey(parameter)) return fallback;
        double value=Convert.ToDouble(configuredParams[parameter]);
        return parameter == "angle_deg" ? value*Math.PI/180 : value*.001;
    }

    static Dictionary<string, object> Configuration(string path)
    {
        var value=Json.Deserialize<Dictionary<string, object>>(File.ReadAllText(path));
        Check(value != null && value.Count == 3 && value.ContainsKey("recipe")
            && value.ContainsKey("parameters") && value.ContainsKey("options"), "Invalid configured authoring fields");
        var parameters=value["parameters"] as Dictionary<string, object>;
        var options=value["options"] as Dictionary<string, object>;
        if(options!=null && options.ContainsKey("program")) {
            string written=value["recipe"] as string;
            Check(new[]{"extrude-two-direction","extrude-midplane","extrude-offset-start","extrude-thin","extrude-up-to",
                "revolve-two-direction","revolve-midplane","revolve-thin","revolve-cut"}.Contains(written),"Unsupported written native recipe");
            Check(parameters!=null && options.Count==4 && options.ContainsKey("basis") && options.ContainsKey("direction")
                && options.ContainsKey("variant"),"Invalid written native case options");
            Check(new[]{"XY","YZ","XZ"}.Contains(options["basis"] as string),"Invalid written native basis");
            Check(options["direction"] is int && ((int)options["direction"]==1 || (int)options["direction"]==-1),"Invalid written native direction");
            CheckProgram(MapValue(options["program"]));
            return value;
        }
        var names=new Dictionary<string, string[]> {
            {"P01",new[]{"width_mm","height_mm"}}, {"P02",new[]{"diameter_mm"}},
            {"P03",new[]{"width_mm","height_mm","depth_mm"}},
            {"P04",new[]{"width_mm","height_mm","depth_mm","cut_width_mm","cut_height_mm","cut_depth_mm"}},
            {"P05",new[]{"inner_radius_mm","outer_radius_mm","height_mm","angle_deg"}}
        };
        string recipe=value["recipe"] as string;
        Check(recipe != null && names.ContainsKey(recipe) && parameters != null
            && parameters.Keys.OrderBy(name=>name).SequenceEqual(names[recipe].OrderBy(name=>name)),
            "Configured parameters differ from the reviewed recipe");
        foreach(var parameter in parameters.Values)
        {
            Check(parameter is int || parameter is long || parameter is double || parameter is decimal,
                "Driving parameters must be numbers");
            double number=Convert.ToDouble(parameter);
            Check(!double.IsNaN(number) && !double.IsInfinity(number) && number>0,
                "Driving parameters must be finite and positive");
        }
        Check(options != null && options.Count==3 && options.ContainsKey("basis")
            && options.ContainsKey("direction") && options.ContainsKey("termination"), "Invalid configured options");
        string basis=options["basis"] as string, termination=options["termination"] as string;
        Check(basis=="XY" || basis=="YZ" || basis=="XZ", "Unsupported configured support basis");
        Check(options["direction"] is int && ((int)options["direction"]==1 || (int)options["direction"]==-1),
            "Configured direction must be integer one or minus one");
        Check(termination=="blind" || termination=="through_all", "Unsupported configured termination");
        Check(recipe=="P03" || (int)options["direction"]==1, "Reverse direction requires P03");
        Check(recipe=="P04" || termination=="blind", "Through all requires P04");
        if(recipe=="P04") Check(Convert.ToDouble(parameters["cut_width_mm"])<Convert.ToDouble(parameters["width_mm"])
            && Convert.ToDouble(parameters["cut_height_mm"])<Convert.ToDouble(parameters["height_mm"])
            && Convert.ToDouble(parameters["cut_depth_mm"])<Convert.ToDouble(parameters["depth_mm"]),
            "Configured cut must remain strictly inside its parent dimensions");
        if(recipe=="P05") Check(basis=="XZ" && Convert.ToDouble(parameters["angle_deg"])<=360
            && Convert.ToDouble(parameters["inner_radius_mm"])<Convert.ToDouble(parameters["outer_radius_mm"]),
            "Configured revolution requires XZ support ordered radii and bounded angle");
        return value;
    }

    public static void CheckConfigured(string path) { Configuration(path); }

    Dictionary<string, object> ConfiguredRecipe(string recipe)
    {
        var original=recipes.Single(row=>(string)row["id"]==recipe);
        var result=Json.Deserialize<Dictionary<string, object>>(Json.Serialize(original));
        result["driving_parameters"]=configuredParams;
        var edits=new List<object>();
        foreach(var parameter in configuredParams)
        {
            if(recipe=="P04" && parameter.Key=="cut_depth_mm"
                && (string)configuredOptions["termination"]=="through_all") continue;
            double current=Convert.ToDouble(parameter.Value), changed=current*1.1;
            if(parameter.Key=="angle_deg") changed=current/2;
            if(parameter.Key=="inner_radius_mm") changed=(current+Convert.ToDouble(configuredParams["outer_radius_mm"]))/2;
            if(parameter.Key.StartsWith("cut_")) {
                string parent=parameter.Key.Substring(4);
                changed=(current+Convert.ToDouble(configuredParams[parent]))/2;
            }
            edits.Add(Row("parameter",parameter.Key,"value",changed));
        }
        result["independent_edits"]=edits;
        return result;
    }

    public static void RunConfigured(object application, string repo, string output, string configuration, string phase)
    {
        Check(phase=="first" || phase=="second", "Configured authoring requires first or second phase");
        var configured=Configuration(configuration);
        var owned=application as ISldWorks;
        Check(owned!=null && owned.GetDocumentCount()==0, "Configured authoring requires an empty owned application");
        var run=new SolidWorksCapture(owned,repo,output);
        run.configuredCase=configured;
        run.configuredParams=(Dictionary<string,object>)configured["parameters"];
        run.configuredOptions=(Dictionary<string,object>)configured["options"];
        string recipe=(string)configured["recipe"], pin=Hash(configuration);
        string directory=Path.Combine(output,recipe), firstPath=Path.Combine(directory,"first.json");
        if(phase=="first") Check(!Directory.Exists(directory), "Select a fresh configured recipe directory");
        else {
            var first=Json.Deserialize<Dictionary<string,object>>(File.ReadAllText(firstPath));
            Check(first.ContainsKey("configuration_sha256") && (string)first["configuration_sha256"]==pin,
                "Configured authoring changed between native phases");
        }
        bool preference=owned.GetUserPreferenceToggle(10);
        owned.SetUserPreferenceToggle(10,false);
        try {
            var specification=run.IsProgram()?null:run.ConfiguredRecipe(recipe);
            if(phase=="first") {
                if(run.IsProgram()) run.ProgramFirst(); else run.First(specification);
                var first=Json.Deserialize<Dictionary<string,object>>(File.ReadAllText(firstPath));
                first["configuration_sha256"]=pin;
                first["configured_case"]=configured;
                Write(firstPath,first);
            } else {
                if(run.IsProgram()) run.ProgramSecond(); else run.Second(specification);
                string measurements=Path.Combine(directory,"measurements.json"), receipt=Path.Combine(directory,"receipt.json");
                var report=Json.Deserialize<Dictionary<string,object>>(File.ReadAllText(measurements));
                report["configuration_sha256"]=pin;
                report["configured_case"]=configured;
                if(RoutineReadback) {
                    report["verification_mode"]="document_reopen";
                    var observed=(Dictionary<string,object>)report["observations"];
                    observed["document_reopen"]=observed["fresh_reopen"];
                    observed.Remove("fresh_reopen");
                }
                report["authoring_origin"]=run.IsProgram()?"Independently authored through typed native operations from the source pinned written recipe"
                    :"Independently authored through the SOLIDWORKS API from the configured paired recipe";
                Write(measurements,report);
                var received=Json.Deserialize<Dictionary<string,object>>(File.ReadAllText(receipt));
                received["measurement_receipt_sha256"]=Hash(measurements);
                received["configuration_sha256"]=pin;
                Write(receipt,received);
            }
            Check(Hash(configuration)==pin, "Configured authoring input changed during execution");
        } finally { owned.SetUserPreferenceToggle(10,preference); }
    }
}
