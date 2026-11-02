// Decompiles every function that references the given addresses (data or code).
// usage (headless): -postScript RefsTo.java <out.c | out.txt> <hex addr> [<hex addr> ...]
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.Function;
import ghidra.program.model.symbol.Reference;
import java.io.FileWriter;
import java.io.PrintWriter;
import java.util.LinkedHashSet;

public class RefsTo extends GhidraScript {
    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        PrintWriter out = new PrintWriter(new FileWriter(args[0]));
        DecompInterface di = new DecompInterface();
        di.openProgram(currentProgram);
        LinkedHashSet<Function> funcs = new LinkedHashSet<>();
        for (int i = 1; i < args.length; i++) {
            out.println("// refs to " + args[i]);
            for (Reference r : getReferencesTo(toAddr(args[i]))) {
                Function f = getFunctionContaining(r.getFromAddress());
                out.println("//   from " + r.getFromAddress() + (f == null ? "" : " in " + f.getName()));
                if (f != null) funcs.add(f);
            }
        }
        if (args[0].endsWith(".txt")) funcs.clear();   // a .txt output lists the references only
        for (Function f : funcs) {
            DecompileResults r = di.decompileFunction(f, 120, monitor);
            out.println("// ===== " + f.getName() + " @ " + f.getEntryPoint());
            out.println(r.decompileCompleted() ? r.getDecompiledFunction().getC() : "// failed: " + r.getErrorMessage());
        }
        out.close();
    }
}
