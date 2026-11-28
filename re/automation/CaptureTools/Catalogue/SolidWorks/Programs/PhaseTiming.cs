// SPDX-License-Identifier: MIT
// SPDX-FileCopyrightText: Copyright (c) 2026 Odin Glynn-Martin, Stephen Harcourt, James Harcourt
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;

public sealed partial class SolidWorksCapture
{
    readonly List<object> StageTimings=new List<object>();
    readonly Stopwatch StageClock=new Stopwatch();
    string StageName;

    void MarkStage(string name)
    {
        if(StageName!=null) StageTimings.Add(Row("stage",StageName,"seconds",StageClock.Elapsed.TotalSeconds));
        StageName=name;
        StageClock.Restart();
    }

    void FinishStages(string phase, bool completed)
    {
        MarkStage(null);
        Write(Path.Combine(output,phase+"-timings.json"),Row("phase",phase,"completed",completed,
            "pid",app.GetProcessID(),"stages",StageTimings));
    }
}
