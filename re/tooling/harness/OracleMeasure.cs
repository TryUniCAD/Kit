using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Runtime.InteropServices;

[ComImport]
[Guid("00020400-0000-0000-C000-000000000046")]
[InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
internal interface INativeDispatch
{
    [PreserveSig]
    int GetTypeInfoCount(out uint count);

    [PreserveSig]
    int GetTypeInfo(uint index, uint locale, out IntPtr info);

    [PreserveSig]
    int GetIDsOfNames(ref Guid iid, [MarshalAs(UnmanagedType.LPArray, ArraySubType = UnmanagedType.LPWStr)] string[] names, int count, uint locale, [Out, MarshalAs(UnmanagedType.LPArray, SizeParamIndex = 2)] int[] ids);

    [PreserveSig]
    int Invoke(int member, ref Guid iid, uint locale, ushort flags, [In] ref DispatchParams parameters, [Out] out object result, [In, Out] ref ExceptionInfo exception, [In, Out] ref int argumentError);
}

[StructLayout(LayoutKind.Sequential)]
internal struct DispatchParams
{
    public IntPtr Arguments;
    public IntPtr NamedArguments;
    public int ArgumentCount;
    public int NamedCount;
}

[StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
internal struct ExceptionInfo
{
    public ushort Code;
    public ushort Reserved;
    [MarshalAs(UnmanagedType.BStr)]
    public string Source;
    [MarshalAs(UnmanagedType.BStr)]
    public string Description;
    [MarshalAs(UnmanagedType.BStr)]
    public string HelpFile;
    public uint HelpContext;
    public IntPtr ReservedPointer;
    public IntPtr DeferredFill;
    public int StatusCode;
}

[StructLayout(LayoutKind.Sequential)]
internal struct NativeVariant
{
    public ushort Type;
    public ushort ReservedOne;
    public ushort ReservedTwo;
    public ushort ReservedThree;
    public IntPtr First;
    public IntPtr Second;
}

internal sealed class ByRefInt
{
    public IntPtr Pointer;
    public int Value()
    {
        return Pointer == IntPtr.Zero ? 0 : Marshal.ReadInt32(Pointer);
    }
}

internal static class OracleMeasure
{
    [DllImport("oleaut32.dll")]
    private static extern int VariantClear(IntPtr variant);

    private static object Invoke(object target, string name, ushort flags, params object[] arguments)
    {
        INativeDispatch dispatch = (INativeDispatch)target;
        int[] identifiers = new int[1];
        Guid emptyGuid = Guid.Empty;
        int resultCode = dispatch.GetIDsOfNames(ref emptyGuid, new[] { name }, 1, 0x0409, identifiers);
        if (resultCode < 0)
        {
            Marshal.ThrowExceptionForHR(resultCode);
        }
        List<IntPtr> allocated = new List<IntPtr>();
        int variantSize = Marshal.SizeOf(typeof(NativeVariant));
        IntPtr namedPointer = IntPtr.Zero;
        try
        {
            IntPtr pointer = IntPtr.Zero;
            if (arguments.Length > 0)
            {
                pointer = Marshal.AllocCoTaskMem(variantSize * arguments.Length);
                allocated.Add(pointer);
                for (int index = 0; index < arguments.Length; index++)
                {
                    IntPtr location = IntPtr.Add(pointer, index * variantSize);
                    object argument = arguments[arguments.Length - index - 1];
                    if (argument is ByRefInt)
                    {
                        ByRefInt reference = (ByRefInt)argument;
                        reference.Pointer = Marshal.AllocCoTaskMem(sizeof(int));
                        allocated.Add(reference.Pointer);
                        Marshal.WriteInt32(reference.Pointer, 0);
                        NativeVariant nativeVariant = new NativeVariant { Type = 0x4003, First = reference.Pointer };
                        Marshal.StructureToPtr(nativeVariant, location, false);
                    }
                    else
                    {
                        Marshal.GetNativeVariantForObject(argument, location);
                    }
                }
            }
            if ((flags & 0x24) != 0)
            {
                namedPointer = Marshal.AllocCoTaskMem(sizeof(int));
                Marshal.WriteInt32(namedPointer, -3);
            }
            DispatchParams parameters = new DispatchParams
            {
                Arguments = pointer,
                NamedArguments = namedPointer,
                ArgumentCount = arguments.Length,
                NamedCount = namedPointer == IntPtr.Zero ? 0 : 1,
            };
            ExceptionInfo exception = new ExceptionInfo();
            int argumentError = 0;
            object value;
            resultCode = dispatch.Invoke(identifiers[0], ref emptyGuid, 0x0409, flags, ref parameters, out value, ref exception, ref argumentError);
            if (resultCode < 0)
            {
                string detail = exception.Description ?? exception.Source;
                Marshal.ThrowExceptionForHR(resultCode);
                throw new InvalidOperationException(detail);
            }
            return value;
        }
        finally
        {
            foreach (IntPtr allocation in allocated)
            {
                for (int index = 0; index < arguments.Length; index++)
                {
                    VariantClear(IntPtr.Add(allocation, index * variantSize));
                }
                Marshal.FreeCoTaskMem(allocation);
            }
            if (namedPointer != IntPtr.Zero)
            {
                Marshal.FreeCoTaskMem(namedPointer);
            }
        }
    }

    private static object Call(object target, string name, params object[] arguments)
    {
        return Invoke(target, name, 3, arguments);
    }

    private static string Number(object value)
    {
        return Convert.ToDouble(value, CultureInfo.InvariantCulture).ToString("R", CultureInfo.InvariantCulture);
    }

    private static string ReportFile;

    private static void Report(string text)
    {
        Console.WriteLine(text);
        if (ReportFile != null)
        {
            File.AppendAllText(ReportFile, text + Environment.NewLine);
        }
    }

    public static int Main(string[] args)
    {
        if (args.Length > 3 || (args.Length >= 1 && !File.Exists(args[0])))
        {
            Console.Error.WriteLine("usage: OracleMeasure existing.SLDPRT|SLDDRW [document_type]");
            return 64;
        }
        int documentType = args.Length >= 2 ? int.Parse(args[1], CultureInfo.InvariantCulture) : 1;
        if (documentType != 1 && documentType != 3)
        {
            Console.Error.WriteLine("document_type must be 1 or 3");
            return 65;
        }
        ReportFile = args.Length == 0
            ? Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "polyline", "drive-oracle.txt")
            : args.Length == 3 ? Path.GetFullPath(args[2]) : null;
        if (ReportFile != null && File.Exists(ReportFile))
        {
            File.Delete(ReportFile);
        }
        object app = null;
        object doc = null;
        try
        {
            Type appType = Type.GetTypeFromProgID("SldWorks.Application");
            if (appType == null)
            {
                Console.Error.WriteLine("SOLIDWORKS is not registered");
                return 69;
            }
            app = Activator.CreateInstance(appType);
            string requestedPath = args.Length == 0 ? string.Empty : Path.GetFullPath(args[0]);
            object activeDocument = Call(app, "ActiveDoc");
            doc = args.Length == 0
                ? activeDocument
                : activeDocument != null && string.Equals(Convert.ToString(Call(activeDocument, "GetPathName")), requestedPath, StringComparison.OrdinalIgnoreCase)
                ? activeDocument
                : null;
            ByRefInt loadErrors = new ByRefInt();
            ByRefInt loadWarnings = new ByRefInt();
            if (doc == null && args.Length > 0)
            {
                doc = Call(app, "OpenDoc6", requestedPath, documentType, 1, 0, "", loadErrors, loadWarnings);
            }
            Report("REVISION=" + Call(app, "RevisionNumber"));
            Report("LOAD_ERRORS=" + loadErrors.Value() + " LOAD_WARNINGS=" + loadWarnings.Value());
            if (doc == null)
            {
                Report("OPENED=False");
                return 2;
            }
            Report("OPENED=True REBUILT=" + Call(doc, "ForceRebuild3", false));
            if (documentType == 3)
            {
                int viewCount = 0;
                for (object view = Call(doc, "GetFirstView"); view != null; view = Call(view, "GetNextView"))
                {
                    viewCount++;
                    Report("VIEW=" + Call(view, "Name") + " TYPE=" + Call(view, "Type"));
                }
                Report("VIEWS=" + viewCount);
                return viewCount > 0 ? 0 : 2;
            }
            object bodyResult = Call(doc, "GetBodies2", 0, true);
            Array bodyArray = bodyResult as Array;
            int bodyCount = bodyArray == null ? (bodyResult == null ? 0 : 1) : bodyArray.Length;
            for (object feature = Call(doc, "FirstFeature"); feature != null; feature = Call(feature, "GetNextFeature"))
            {
                string typeName = Convert.ToString(Call(feature, "GetTypeName2"), CultureInfo.InvariantCulture);
                Report("FEATURE=" + Call(feature, "Name") + " TYPE=" + typeName);
                if (typeName == "SolidBodyFolder")
                {
                    for (object bodyFeature = Call(feature, "GetFirstSubFeature"); bodyFeature != null; bodyFeature = Call(bodyFeature, "GetNextSubFeature"))
                    {
                        bodyCount++;
                        Report("BODY=" + Call(bodyFeature, "Name") + " TYPE=" + Call(bodyFeature, "GetTypeName2"));
                    }
                }
            }
            Report("BODIES=" + bodyCount);
            object extension = Call(doc, "Extension");
            object mass = Call(extension, "CreateMassProperty");
            Report("VOLUME_MM3=" + Number(Convert.ToDouble(Call(mass, "Volume")) * 1000000000.0));
            Report("AREA_MM2=" + Number(Convert.ToDouble(Call(mass, "SurfaceArea")) * 1000000.0));
            double[] center = (double[])Call(mass, "CenterOfMass");
            Report("COM_MM=" + Number(center[0] * 1000.0) + "," + Number(center[1] * 1000.0) + "," + Number(center[2] * 1000.0));
            try
            {
                object dimension = Call(doc, "Parameter", "D1@Boss-Extrude1");
                if (dimension != null)
                {
                    Report("DEPTH_PARAMETER=" + Number(Convert.ToDouble(Call(dimension, "SystemValue")) * 1000.0));
                }
            }
            catch (Exception error)
            {
                Report("DEPTH_PARAMETER=UNAVAILABLE " + error.GetType().Name);
            }
            return bodyCount > 0 ? 0 : 2;
        }
        catch (Exception error)
        {
            Report("ORACLE_ERROR=" + error);
            return 1;
        }
        finally
        {
            if (app != null && doc != null)
            {
                Call(app, "CloseDoc", Call(doc, "GetTitle"));
            }
        }
    }
}
