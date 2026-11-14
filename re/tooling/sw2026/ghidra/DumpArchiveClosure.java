import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;
import java.io.PrintWriter;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Deque;
import java.util.HashSet;
import java.util.Iterator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileOptions;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.pcode.HighFunction;
import ghidra.program.model.pcode.HighParam;
import ghidra.program.model.pcode.HighSymbol;
import ghidra.program.model.pcode.HighVariable;
import ghidra.program.model.pcode.LocalSymbolMap;
import ghidra.program.model.pcode.PcodeOp;
import ghidra.program.model.pcode.PcodeOpAST;
import ghidra.program.model.pcode.Varnode;

public class DumpArchiveClosure extends GhidraScript {

    static class Item {
        Function f;
        int slot;
        int depth;
        Item(Function f, int slot, int depth) { this.f = f; this.slot = slot; this.depth = depth; }
    }

    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        File outputFile = new File(args[0]);
        int maxDepth = Integer.parseInt(args[2]);
        int timeout = args.length > 3 ? Integer.parseInt(args[3]) : 180;
        Deque<Item> queue = new ArrayDeque<>();
        Map<String, Item> plan = new LinkedHashMap<>();
        for (String raw : Files.readAllLines(Paths.get(args[1]))) {
            String text = raw.trim();
            if (text.isEmpty() || text.startsWith("#")) continue;
            String[] parts = text.split("\\s+");
            String hex = parts[0].startsWith("0x") ? parts[0].substring(2) : parts[0];
            int slot = parts.length > 1 ? Integer.parseInt(parts[1]) : 1;
            Address a = currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(Long.parseLong(hex, 16));
            Function f = getFunctionAt(a);
            if (f == null) f = getFunctionContaining(a);
            if (f == null) { println("NO FUNCTION " + text); continue; }
            String key = f.getEntryPoint().toString() + ":" + slot;
            if (!plan.containsKey(key)) {
                Item it = new Item(f, slot, 0);
                plan.put(key, it);
                queue.add(it);
            }
        }
        DecompInterface dec = new DecompInterface();
        DecompileOptions options = new DecompileOptions();
        options.setMaxWidth(160);
        dec.setOptions(options);
        dec.toggleCCode(true);
        dec.toggleSyntaxTree(true);
        dec.setSimplificationStyle("decompile");
        dec.openProgram(currentProgram);
        outputFile.getParentFile().mkdirs();
        PrintWriter w = new PrintWriter(new BufferedWriter(new FileWriter(outputFile)));
        Set<String> written = new HashSet<>();
        while (!queue.isEmpty() && !monitor.isCancelled()) {
            Item it = queue.poll();
            DecompileResults r = dec.decompileFunction(it.f, timeout, monitor);
            String ep = it.f.getEntryPoint().toString();
            List<String> edges = new ArrayList<>();
            if (r != null && r.decompileCompleted() && r.getHighFunction() != null) {
                HighFunction hf = r.getHighFunction();
                Set<Varnode> arch = archiveVarnodes(hf, it.slot);
                Iterator<PcodeOpAST> ops = hf.getPcodeOps();
                while (ops.hasNext()) {
                    PcodeOpAST op = ops.next();
                    int oc = op.getOpcode();
                    if (oc != PcodeOp.CALL && oc != PcodeOp.CALLIND) continue;
                    for (int i = 1; i < op.getNumInputs(); i++) {
                        if (!arch.contains(op.getInput(i))) continue;
                        if (oc == PcodeOp.CALLIND) {
                            String nm = refName(op.getSeqnum().getTarget());
                            edges.add((nm == null ? "INDIRECT" : "EXT " + nm) + "@" + op.getSeqnum().getTarget() + " slot=" + (i - 1));
                            continue;
                        }
                        Address ca = op.getInput(0).getAddress();
                        Function callee = currentProgram.getFunctionManager().getFunctionAt(ca);
                        if (callee == null) {
                            ghidra.program.model.symbol.Symbol sy = getSymbolAt(ca);
                            edges.add("EXT " + (sy == null ? ca.toString() : sy.getName(true)) + "@" + ca + " slot=" + (i - 1));
                            continue;
                        }
                        String nm = callee.getName(true);
                        boolean ext = callee.isExternal() || callee.isThunk();
                        edges.add((ext ? "EXT " : "CALL ") + nm + "@" + callee.getEntryPoint() + " slot=" + (i - 1));
                        if (ext || it.depth + 1 > maxDepth) continue;
                        String key = callee.getEntryPoint().toString() + ":" + (i - 1);
                        if (!plan.containsKey(key)) {
                            Item nx = new Item(callee, i - 1, it.depth + 1);
                            plan.put(key, nx);
                            queue.add(nx);
                        }
                    }
                }
            }
            if (!written.add(ep)) continue;
            w.println();
            w.println("=== FUNCTION " + it.f.getName(true));
            w.println("=== ADDRESS " + ep);
            w.println("=== DEPTH " + it.depth + " ARCHIVE_SLOT " + it.slot);
            for (String e : edges) w.println("=== EDGE " + e);
            if (r != null && r.decompileCompleted() && r.getDecompiledFunction() != null) {
                w.println(r.getDecompiledFunction().getC());
            } else {
                w.println("=== DECOMPILE FAILED");
            }
            w.flush();
        }
        w.println("=== SUMMARY planned=" + plan.size() + " written=" + written.size());
        w.close();
        dec.dispose();
    }

    String refName(Address at) {
        for (ghidra.program.model.symbol.Reference ref : getReferencesFrom(at)) {
            Address to = ref.getToAddress();
            ghidra.program.model.symbol.Symbol sym = getSymbolAt(to);
            if (ref.isExternalReference() || to.isExternalAddress()) {
                if (sym != null) return sym.getName(true);
            }
            for (ghidra.program.model.symbol.Reference r2 : getReferencesFrom(to)) {
                ghidra.program.model.symbol.Symbol s2 = getSymbolAt(r2.getToAddress());
                if (s2 != null && r2.getToAddress().isExternalAddress()) return s2.getName(true);
            }
            if (sym != null && !sym.getName().startsWith("DAT_") && !sym.getName().startsWith("LAB_")) return sym.getName(true);
        }
        return null;
    }

    Set<Varnode> archiveVarnodes(HighFunction hf, int slot) {
        Set<Varnode> out = new HashSet<>();
        LocalSymbolMap lsm = hf.getLocalSymbolMap();
        HighVariable hv = null;
        for (int i = 0; i < lsm.getNumParams(); i++) {
            HighSymbol s = lsm.getParamSymbol(i);
            if (s != null && s.getCategoryIndex() == slot) {
                hv = s.getHighVariable();
            }
        }
        if (hv == null) return out;
        for (Varnode v : hv.getInstances()) out.add(v);
        boolean grew = true;
        while (grew) {
            grew = false;
            Iterator<PcodeOpAST> ops = hf.getPcodeOps();
            while (ops.hasNext()) {
                PcodeOpAST op = ops.next();
                int oc = op.getOpcode();
                if (oc != PcodeOp.COPY && oc != PcodeOp.CAST && oc != PcodeOp.MULTIEQUAL && oc != PcodeOp.INDIRECT) continue;
                Varnode o = op.getOutput();
                if (o == null || out.contains(o)) continue;
                for (int i = 0; i < op.getNumInputs(); i++) {
                    if (out.contains(op.getInput(i))) {
                        out.add(o);
                        HighVariable h = o.getHigh();
                        if (h != null) for (Varnode v : h.getInstances()) out.add(v);
                        grew = true;
                        break;
                    }
                }
            }
        }
        return out;
    }
}
