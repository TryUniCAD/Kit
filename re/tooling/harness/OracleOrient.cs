using System;
using System.Reflection;

class OracleOrient
{
    static BindingFlags Flags = BindingFlags.InvokeMethod | BindingFlags.GetProperty | BindingFlags.Public | BindingFlags.Instance;

    static object Call(object Target, string Name, params object[] Args)
    {
        return Target.GetType().InvokeMember(Name, Flags, null, Target, Args);
    }

    static string Text(object Target, string Name)
    {
        object Value = Call(Target, Name);
        return Value == null ? "" : Value.ToString();
    }

    static void Dump(string Label, object Value)
    {
        if (Value == null) { Console.WriteLine(Label + "=null"); return; }
        Array Items = Value as Array;
        if (Items == null) { Console.WriteLine(Label + "=" + Value); return; }
        string Line = Label + "=";
        for (int Index = 0; Index < Items.Length; Index++)
        {
            if (Index > 0) Line += ",";
            Line += Items.GetValue(Index).ToString();
        }
        Console.WriteLine(Line);
    }

    static void Main(string[] Args)
    {
        Type AppType = Type.GetTypeFromProgID("SldWorks.Application");
        object App = Activator.CreateInstance(AppType);
        object Doc = Call(App, "OpenDoc", Args[0], 3);
        object View = Call(Doc, "GetFirstView");
        while (View != null)
        {
            Console.WriteLine("VIEW=" + Text(View, "Name") + " TYPE=" + Text(View, "Type"));
            foreach (string Name in new string[] { "GetOrientation", "GetXform", "GetViewXform" })
            {
                try
                {
                    object Result = Call(View, Name);
                    if (Result == null) { Console.WriteLine(Name + "=null"); continue; }
                    if (Result is Array) { Dump(Name, Result); continue; }
                    try { Dump(Name + ".ArrayData", Call(Result, "ArrayData")); }
                    catch (Exception) { Console.WriteLine(Name + "=" + Result.GetType().ToString()); }
                }
                catch (Exception Error) { Console.WriteLine(Name + "_ERROR=" + Error.Message); }
            }
            View = Call(View, "GetNextView");
        }
        try { Call(App, "CloseDoc", Text(Doc, "Title")); } catch (Exception) { }
    }
}
