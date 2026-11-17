// SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
// SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
//
// This SPDX license identifier and copyright notice must not be
// removed, altered, or obscured. Doing so is a material breach of
// the PolyForm Strict License 1.0.0 and voids all licenses granted
// to you under it immediately and permanently.

using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Security.Cryptography;
using System.Text;
using System.Web.Script.Serialization;

public sealed class ReadbackProgress
{
    const int Limit = 1024 * 1024;
    readonly JavaScriptSerializer json = new JavaScriptSerializer { MaxJsonLength = Limit };
    readonly string path;
    readonly Dictionary<string, object> binding;
    string previous;
    string writeError;
    int sequence;
    long totalBytes;

    public ReadbackProgress(string path, Dictionary<string, object> launch)
    {
        this.path = path;
        if (path == null) return;
        if (launch == null) throw new InvalidOperationException("Progress requires a directly owned launch");
        binding = new Dictionary<string, object> {
            { "source_revision", launch["source_revision"] }, { "request_sha256", launch["request_sha256"] },
            { "process", new Dictionary<string, object> {
                { "pid", launch["pid"] }, { "created", launch["created"] },
                { "session", launch["session"] }, { "image", launch["image"] } } }
        };
        using (var created = new FileStream(path, FileMode.CreateNew, FileAccess.Write, FileShare.Read)) created.Flush(true);
    }

    public static string Digest(byte[] content)
    {
        using (var hash = SHA256.Create())
            return BitConverter.ToString(hash.ComputeHash(content)).Replace("-", "").ToLowerInvariant();
    }

    void Record(string stage, string file, string status, object detail)
    {
        if (path == null || writeError != null) return;
        try
        {
            var row = new Dictionary<string, object> {
                { "sequence", sequence + 1 }, { "previous_sha256", previous }, { "binding", binding },
                { "stage", stage }, { "file", file }, { "status", status }, { "detail", detail },
                { "recorded_utc", DateTime.UtcNow.ToString("O", CultureInfo.InvariantCulture) }
            };
            byte[] content = Encoding.UTF8.GetBytes(json.Serialize(row) + "\n");
            if (sequence >= 1024 || content.Length > 16384 || totalBytes + content.Length > Limit)
                throw new InvalidOperationException("Native progress exceeds its bounded journal");
            using (var stream = new FileStream(path, FileMode.Append, FileAccess.Write, FileShare.Read))
            {
                if (stream.Length != totalBytes) throw new InvalidOperationException("Native progress journal changed");
                stream.Write(content, 0, content.Length);
                stream.Flush(true);
            }
            previous = Digest(content);
            sequence++;
            totalBytes += content.Length;
        }
        catch (Exception error)
        {
            writeError = error.GetType().Name + ":" + error.HResult.ToString(CultureInfo.InvariantCulture);
        }
    }

    public T Invoke<T>(string stage, string file, Func<T> action)
    {
        Record(stage, file, "started", null);
        try
        {
            T value = action();
            Record(stage, file, "completed", null);
            return value;
        }
        catch (Exception error)
        {
            Record(stage, file, "failed", new Dictionary<string, object> {
                { "type", error.GetType().Name }, { "hresult", error.HResult }
            });
            throw;
        }
    }

    public void Invoke(string stage, string file, Action action)
    {
        Invoke(stage, file, () => { action(); return true; });
    }

    public object Finish(string outcome)
    {
        if (path == null) return null;
        Record("run", null, outcome == "observed" ? "completed" : "failed",
            new Dictionary<string, object> { { "outcome", outcome } });
        byte[] content;
        using (var reader = new BinaryReader(File.OpenRead(path))) content = reader.ReadBytes(Limit + 1);
        if (content.Length > Limit) throw new InvalidOperationException("Native progress exceeds its byte limit");
        return new Dictionary<string, object> {
            { "version", 1 }, { "journal_utf8", Encoding.UTF8.GetString(content) },
            { "sha256", Digest(content) }, { "events", sequence }, { "write_error", writeError }
        };
    }
}
