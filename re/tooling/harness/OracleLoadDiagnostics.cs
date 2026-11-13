using System;
using System.IO;
using SolidWorks.Interop.sldworks;

internal static class OracleLoadDiagnostics
{
    private static int Main(string[] args)
    {
        if (args.Length != 1 || !File.Exists(args[0]))
        {
            Console.Error.WriteLine("usage: OracleLoadDiagnostics existing.SLDPRT");
            return 64;
        }
        Type applicationType = Type.GetTypeFromProgID("SldWorks.Application");
        SldWorks application = (SldWorks)Activator.CreateInstance(applicationType);
        Console.WriteLine("REVISION=" + application.RevisionNumber());
        Console.WriteLine("DOCUMENT_COUNT=" + application.GetDocumentCount());
        Array documents = (Array)application.GetDocuments();
        Console.WriteLine("DOCUMENT_ARRAY=" + (documents == null ? 0 : documents.Length));
        if (documents != null) foreach (ModelDoc2 openDocument in documents)
        {
            Console.WriteLine("OPEN_DOCUMENT=" + (openDocument == null ? "null" : openDocument.GetTitle()));
        }
        int errors = 0;
        int warnings = 0;
        ModelDoc2 document = application.OpenDoc6(Path.GetFullPath(args[0]), 1, 1, "", ref errors, ref warnings);
        Console.WriteLine("LOAD_ERRORS=" + errors + " LOAD_WARNINGS=" + warnings);
        if (document == null)
        {
            Console.WriteLine("OPENED=False");
            return 2;
        }
        try
        {
            Console.WriteLine("OPENED=True REBUILT=" + document.ForceRebuild3(false));
            Array bodies = (Array)((PartDoc)document).GetBodies2(0, true);
            Console.WriteLine("BODIES=" + (bodies == null ? 0 : bodies.Length));
            dynamic properties = document.Extension.CreateMassProperty();
            Console.WriteLine("VOLUME_MM3=" + properties.Volume * 1000000000.0);
            Console.WriteLine("AREA_MM2=" + properties.SurfaceArea * 1000000.0);
            double[] centre = (double[])properties.CenterOfMass;
            Console.WriteLine("COM_MM=" + centre[0] * 1000.0 + "," + centre[1] * 1000.0 + "," + centre[2] * 1000.0);
            dynamic dimension = document.Parameter("D1@Boss-Extrude1");
            if (dimension != null)
            {
                Console.WriteLine("DEPTH_PARAMETER=" + dimension.SystemValue * 1000.0);
            }
            return bodies != null && bodies.Length > 0 ? 0 : 2;
        }
        finally
        {
            application.CloseDoc(document.GetTitle());
        }
    }
}
