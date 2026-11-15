using System;
using System.Reflection;

class OraclePolylines
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

    static void Main(string[] Args)
    {
        Type AppType = Type.GetTypeFromProgID("SldWorks.Application");
        object App = Activator.CreateInstance(AppType);
        object Doc = Call(App, "OpenDoc", Args[0], 3);
        object View = Call(Doc, "GetFirstView");
        while (View != null)
        {
            string Name = Text(View, "Name");
            string TypeValue = Text(View, "Type");
            Console.WriteLine("VIEW=" + Name + " TYPE=" + TypeValue);
            try
            {
                object Count = Call(View, "GetPolyLineCount5", (short)0);
                Console.WriteLine("COUNT=" + Count);
            }
            catch (Exception Error) { Console.WriteLine("COUNT_ERROR=" + Error.Message); }
            try
            {
                object Result = Call(View, "GetPolylines5", (short)0);
                Array Outer = Result as Array;
                if (Outer == null) { Console.WriteLine("POLY=None"); }
                else
                {
                    Console.WriteLine("DOUBLES=" + Outer.Length);
                    string Line = "";
                    for (int Index = 0; Index < Outer.Length; Index++)
                    {
                        object Item = Outer.GetValue(Index);
                        Line += Item.ToString() + (Index + 1 == Outer.Length ? "" : ",");
                    }
                    Console.WriteLine(Line);
                }
            }
            catch (Exception Error) { Console.WriteLine("POLY_ERROR=" + Error.Message); }
            View = Call(View, "GetNextView");
        }
        try { Call(App, "CloseDoc", Text(Doc, "Title")); }
        catch (Exception) { }
    }
}
