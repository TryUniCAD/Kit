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
        if (Doc == null)
        {
            Console.WriteLine("OPENED=False");
            return;
        }
        object View = Call(Doc, "GetFirstView");
        while (View != null)
        {
            string Name = Text(View, "Name");
            string TypeValue = Text(View, "Type");
            Console.WriteLine("VIEW=" + Name + " TYPE=" + TypeValue);
            try
            {
                object Outline = Call(View, "GetOutline");
                Array Box = Outline as Array;
                if (Box == null)
                {
                    Console.WriteLine("OUTLINE=None " + (Outline == null ? "null" : Outline.GetType().ToString()));
                }
                else
                {
                    string Line = "OUTLINE=";
                    for (int Index = 0; Index < Box.Length; Index++)
                    {
                        if (Index > 0) Line += ",";
                        Line += Box.GetValue(Index).ToString();
                    }
                    Console.WriteLine(Line);
                }
            }
            catch (Exception Error)
            {
                Console.WriteLine("OUTLINE_ERROR=" + Error.Message);
            }
            try
            {
                object Result = Call(View, "GetPolylines5", (short)0);
                Array Outer = Result as Array;
                if (Outer == null)
                {
                    Console.WriteLine("POLY=None " + (Result == null ? "null" : Result.GetType().ToString()));
                }
                else
                {
                    Console.WriteLine("POLY_TOTAL=" + Outer.Length);
                    for (int Index = 0; Index < Outer.Length && Index < 8; Index++)
                    {
                        object Item = Outer.GetValue(Index);
                        Array Inner = Item as Array;
                        if (Inner == null)
                        {
                            Console.WriteLine("POLY=" + Index + " SCALAR=" + Item);
                            continue;
                        }
                        string Line = "POLY=" + Index + " N=" + Inner.Length;
                        for (int Point = 0; Point < Inner.Length && Point < 16; Point++)
                        {
                            Line += " " + Inner.GetValue(Point).ToString();
                        }
                        Console.WriteLine(Line);
                    }
                }
            }
            catch (Exception Error)
            {
                Console.WriteLine("POLY_ERROR=" + Error.Message);
            }
            View = Call(View, "GetNextView");
        }
        Call(App, "CloseDoc", Text(Doc, "Title"));
    }
}
