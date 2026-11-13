using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Globalization;
using System.IO;
using System.Threading;

internal static class TraceSession
{
    private static int EventCount(string path)
    {
        if (!File.Exists(path))
        {
            return 0;
        }
        int count = 0;
        using (FileStream stream = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.ReadWrite | FileShare.Delete))
        using (StreamReader reader = new StreamReader(stream))
        {
            string line;
            while ((line = reader.ReadLine()) != null)
            {
                if (line.StartsWith("RO ", StringComparison.Ordinal) || line.StartsWith("RC ", StringComparison.Ordinal) || line.StartsWith("F ", StringComparison.Ordinal))
                {
                    count++;
                }
            }
        }
        return count;
    }

    public static int Main(string[] args)
    {
        if (args.Length < 3 || args.Length > 7)
        {
            Console.Error.WriteLine("usage: TraceSession log script part [hard_seconds quiet_seconds]");
            return 64;
        }
        string logPath = Path.GetFullPath(args[0]);
        string scriptPath = Path.GetFullPath(args[1]);
        string partPath = Path.GetFullPath(args[2]);
        int hardSeconds = args.Length > 3 ? int.Parse(args[3], CultureInfo.InvariantCulture) : 300;
        int quietSeconds = args.Length > 4 ? int.Parse(args[4], CultureInfo.InvariantCulture) : 45;
        int attachPid = args.Length > 5 ? int.Parse(args[5], CultureInfo.InvariantCulture) : 0;
        string alternateOracle = args.Length > 6 ? args[6] : null;
        string debuggerPath = @"C:\Users\odin\Documents\kit-re\debuggers\cdb.exe";
        string executablePath = @"C:\Program Files\SOLIDWORKS Corp\SOLIDWORKS\SLDWORKS.exe";
        if (!File.Exists(logPath) && !Directory.Exists(Path.GetDirectoryName(logPath)) || !File.Exists(scriptPath) || !File.Exists(partPath) || !File.Exists(debuggerPath) || !File.Exists(executablePath) || hardSeconds <= 0 || quietSeconds <= 0 || quietSeconds >= hardSeconds)
        {
            Console.Error.WriteLine("invalid trace inputs or time bounds");
            return 65;
        }
        HashSet<int> original = new HashSet<int>();
        foreach (Process process in Process.GetProcessesByName("SLDWORKS"))
        {
            original.Add(process.Id);
            process.Dispose();
        }
        if (File.Exists(logPath))
        {
            File.Delete(logPath);
        }
        Stopwatch timer = Stopwatch.StartNew();
        string traceArguments = "-logo \"" + logPath + "\" -c \"$$<" + scriptPath + "\"";
        traceArguments = attachPid > 0 ? traceArguments + " -p " + attachPid.ToString(CultureInfo.InvariantCulture) : traceArguments + " \"" + executablePath + "\" \"" + partPath + "\"";
        ProcessStartInfo startInfo = new ProcessStartInfo
        {
            FileName = debuggerPath,
            Arguments = traceArguments,
            WorkingDirectory = Path.GetDirectoryName(logPath),
            UseShellExecute = false,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            CreateNoWindow = true,
        };
        Process debugger = new Process { StartInfo = startInfo };
        debugger.OutputDataReceived += delegate { };
        debugger.ErrorDataReceived += delegate { };
        string status = "running";
        int events = 0;
        TimeSpan lastChange = timer.Elapsed;
        try
        {
            if (!debugger.Start())
            {
                throw new InvalidOperationException("cdb failed to start");
            }
            Console.WriteLine("TRACE_PID=" + debugger.Id);
            debugger.BeginOutputReadLine();
            debugger.BeginErrorReadLine();
            if (attachPid > 0)
            {
                string oraclePath = alternateOracle ?? Path.GetFullPath(Path.Combine(Path.GetDirectoryName(logPath), "..", "OracleMeasure.exe"));
                if (!File.Exists(oraclePath))
                {
                    throw new FileNotFoundException("oracle reader is missing", oraclePath);
                }
                Thread.Sleep(TimeSpan.FromSeconds(15));
                ProcessStartInfo oracleStart = new ProcessStartInfo
                {
                    FileName = oraclePath,
                    Arguments = "\"" + partPath + "\"",
                    UseShellExecute = false,
                    RedirectStandardOutput = true,
                    RedirectStandardError = true,
                    CreateNoWindow = true,
                };
                using (Process oracle = Process.Start(oracleStart))
                {
                    oracle.OutputDataReceived += delegate { };
                    oracle.ErrorDataReceived += delegate { };
                    oracle.BeginOutputReadLine();
                    oracle.BeginErrorReadLine();
                    if (!oracle.WaitForExit(120000))
                    {
                        oracle.Kill();
                        throw new TimeoutException("oracle document read timed out");
                    }
                    Console.WriteLine("ORACLE_EXIT=" + oracle.ExitCode);
                }
            }
            while (!debugger.HasExited)
            {
                int current = EventCount(logPath);
                if (current != events)
                {
                    events = current;
                    lastChange = timer.Elapsed;
                }
                if (events > 0 && timer.Elapsed - lastChange >= TimeSpan.FromSeconds(quietSeconds))
                {
                    status = "quiet";
                    break;
                }
                if (timer.Elapsed >= TimeSpan.FromSeconds(hardSeconds))
                {
                    status = "deadline";
                    break;
                }
                Thread.Sleep(TimeSpan.FromSeconds(2));
            }
            if (debugger.HasExited)
            {
                events = EventCount(logPath);
                status = "cdb-exited";
            }
        }
        finally
        {
            foreach (Process process in Process.GetProcessesByName("SLDWORKS"))
            {
                try
                {
                    if (!original.Contains(process.Id))
                    {
                        process.Kill();
                        process.WaitForExit(30000);
                    }
                }
                catch (Exception error)
                {
                    Console.Error.WriteLine("TARGET_CLEANUP=" + process.Id + " " + error.GetType().Name);
                }
                finally
                {
                    process.Dispose();
                }
            }
            if (!debugger.HasExited)
            {
                debugger.Kill();
                debugger.WaitForExit(30000);
            }
        }
        debugger.Dispose();
        Console.WriteLine("TRACE_STATUS=" + status + " EVENTS=" + events + " SECONDS=" + timer.Elapsed.TotalSeconds.ToString("R", CultureInfo.InvariantCulture) + " LOG=" + logPath);
        return events > 0 ? 0 : 3;
    }
}
