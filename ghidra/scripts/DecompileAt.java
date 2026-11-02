// Decompiles the functions containing the given addresses and writes the C to a file.
// usage (headless): -postScript DecompileAt.java <out.c> <hex addr> [<hex addr> ...]
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import java.io.FileWriter;
import java.io.PrintWriter;

public class DecompileAt extends GhidraScript {
    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        PrintWriter out = new PrintWriter(new FileWriter(args[0]));
        DecompInterface di = new DecompInterface();
        di.openProgram(currentProgram);
        for (int i = 1; i < args.length; i++) {
            Address a = toAddr(args[i]);
            Function f = getFunctionContaining(a);
            if (f == null) {                       // code only reached through a table built at run
                disassemble(a);                    // time: make the function here (not saved: -readOnly)
                f = createFunction(a, null);
            }
            if (f == null) {
                out.println("// no function at " + args[i]);
                continue;
            }
            DecompileResults r = di.decompileFunction(f, 120, monitor);
            out.println("// ===== " + args[i] + " in " + f.getName() + " @ " + f.getEntryPoint());
            out.println(r.decompileCompleted() ? r.getDecompiledFunction().getC() : "// failed: " + r.getErrorMessage());
        }
        out.close();
    }
}
