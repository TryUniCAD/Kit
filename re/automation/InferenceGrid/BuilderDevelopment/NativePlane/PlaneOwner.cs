// SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
// SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
//
// This SPDX license identifier and copyright notice must not be
// removed, altered, or obscured. Doing so is a material breach of
// the PolyForm Strict License 1.0.0 and voids all licenses granted
// to you under it immediately and permanently.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Runtime.InteropServices;
using System.Text;
using System.Web.Script.Serialization;
using SolidWorks.Interop.sldworks;

public static class PlaneOwner
{
    public static void Run(Process Process,string Executable,string Repository,string Output,string Manifest,string Phase)
    {
        ISldWorks Application=null; Exception Failure=null;
        var Errors=new List<string>();
        var Record=new Dictionary<string,object> {{"pid",Process.Id},{"phase",Phase},{"initial_documents",null},
            {"background_control",false},{"normal_exit_requested",false},{"cleanup_errors",Errors}};
        try {
            Application=SolidOwner.AttachOwned(Process,Executable,120);
            Record["initial_documents"]=Application.GetDocumentCount();
            if((int)Record["initial_documents"]!=0) throw new InvalidOperationException("Candidate requires an empty owned native session");
            Application.UserControlBackground=true; Record["background_control"]=Application.UserControlBackground;
            if(!(bool)Record["background_control"]) throw new InvalidOperationException("Native background lifetime control did not persist");
            Application.Visible=false;
            SolidWorksCapture.RunPlane(Application,Repository,Output,Manifest,Phase);
        } catch(Exception Error) { Failure=Error; Record["failure"]=Error.ToString(); }
        finally {
            if(Application!=null) {
                try { if(Application.GetProcessID()==Process.Id && Application.GetDocumentCount()==0) {
                    Application.ExitApp(); Record["normal_exit_requested"]=true;
                }} catch(Exception Error) { Errors.Add(Error.ToString()); }
                try { Marshal.FinalReleaseComObject(Application); } catch(Exception Error) { Errors.Add(Error.ToString()); }
            }
            Directory.CreateDirectory(Output);
            using(var Stream=new FileStream(Path.Combine(Output,Phase+"-native.json"),FileMode.CreateNew,FileAccess.Write,FileShare.None)) {
                byte[] Raw=new UTF8Encoding(false).GetBytes(new JavaScriptSerializer().Serialize(Record)+"\n");
                Stream.Write(Raw,0,Raw.Length); Stream.Flush(true);
            }
        }
        if(Failure!=null) throw new InvalidOperationException("Candidate plane phase failed: "+Failure.Message,Failure);
        if(Errors.Count!=0 || !(bool)Record["normal_exit_requested"]) throw new InvalidOperationException("Candidate native cleanup did not complete normally");
    }
}
