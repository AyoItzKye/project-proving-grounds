// Finds a string in memory and decompiles every function that references it.
// usage (headless): -postScript StringRefs.java <out.c> <string> [sub]
//   default: the exact ASCII string (null-terminated)
//   sub:     every ASCII or UTF-16 string CONTAINING the text (Oct 25: "motion_tracker" sat inside longer names);
//            each whole string is listed with its references, then at most MAX_FUNCS functions are decompiled
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.mem.Memory;
import ghidra.program.model.symbol.Reference;
import java.io.FileWriter;
import java.io.PrintWriter;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.Map;

public class StringRefs extends GhidraScript {
    static final int MAX_FUNCS = 40;

    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        PrintWriter out = new PrintWriter(new FileWriter(args[0]));
        boolean sub = args.length > 2 && args[2].equals("sub");
        Map<Address, String> starts = new LinkedHashMap<>();   // string start -> its text ("U:" = UTF-16)
        if (!sub) {
            byte[] want = (args[1] + "\0").getBytes("US-ASCII");
            for (Address a = currentProgram.getMinAddress(); (a = find(a, want)) != null; a = a.add(1))
                starts.put(a, args[1]);
        } else {
            for (int width = 1; width <= 2; width++) {
                byte[] want = args[1].getBytes(width == 1 ? "US-ASCII" : "UTF-16LE");
                for (Address a = currentProgram.getMinAddress(); (a = find(a, want)) != null; a = a.add(1)) {
                    Address s = stringStart(a, width);
                    if (!starts.containsKey(s))
                        starts.put(s, (width == 2 ? "U:" : "") + readString(s, width));
                }
            }
        }
        LinkedHashSet<Function> funcs = new LinkedHashSet<>();
        for (Map.Entry<Address, String> e : starts.entrySet()) {
            out.println("// string at " + e.getKey() + "  \"" + e.getValue() + "\"");
            for (Reference r : getReferencesTo(e.getKey())) {
                Function f = getFunctionContaining(r.getFromAddress());
                out.println("//   ref from " + r.getFromAddress() + (f == null ? "" : " in " + f.getName()));
                if (f != null) funcs.add(f);
            }
        }
        out.println("// " + starts.size() + " strings, " + funcs.size() + " referencing functions"
                    + (funcs.size() > MAX_FUNCS ? " (decompiling the first " + MAX_FUNCS + ")" : ""));
        DecompInterface di = new DecompInterface();
        di.openProgram(currentProgram);
        int n = 0;
        for (Function f : funcs) {
            if (n++ >= MAX_FUNCS) break;
            DecompileResults r = di.decompileFunction(f, 120, monitor);
            out.println("// ===== " + f.getName() + " @ " + f.getEntryPoint());
            out.println(r.decompileCompleted() ? r.getDecompiledFunction().getC() : "// failed: " + r.getErrorMessage());
        }
        out.close();
    }

    // a printable character of the given width (UTF-16 here: ASCII range with a zero high byte)
    boolean printable(Address a, int width) {
        try {
            Memory m = currentProgram.getMemory();
            int lo = m.getByte(a) & 0xFF;
            return lo >= 0x20 && lo < 0x7F && (width == 1 || m.getByte(a.add(1)) == 0);
        } catch (Exception ex) {
            return false;
        }
    }

    Address stringStart(Address a, int width) {
        while (true) {
            try {
                Address p = a.subtract(width);
                if (!printable(p, width)) return a;
                a = p;
            } catch (Exception ex) {
                return a;
            }
        }
    }

    String readString(Address a, int width) {
        StringBuilder sb = new StringBuilder();
        try {
            while (sb.length() < 200 && printable(a, width)) {
                sb.append((char) (currentProgram.getMemory().getByte(a) & 0xFF));
                a = a.add(width);
            }
        } catch (Exception ex) {
            // the end of the block ends the string
        }
        return sb.toString();
    }
}
