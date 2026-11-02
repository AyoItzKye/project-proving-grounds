// Lists the functions whose instructions use every given constant as an operand (e.g. CE's
// game_engine_player_should_spawn compares the respawn timer with 90, 60 and 30), then decompiles them.
// usage (headless): -postScript FindConsts.java <out.c> [any] [range <hex lo> <hex hi>] <hex const> [...]
//   any: constants in any instruction, not only CMP (a compiler turns == 90 / 60 / 30 into SUB chains)
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.scalar.Scalar;
import java.io.FileWriter;
import java.io.PrintWriter;
import java.util.HashSet;
import java.util.Set;

public class FindConsts extends GhidraScript {
    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        PrintWriter out = new PrintWriter(new FileWriter(args[0]));
        Set<Long> want = new HashSet<>();
        boolean any = false;
        long lo = 0, hi = Long.MAX_VALUE;     // range <hex lo> <hex hi>: functions in that range ("=" splits .bat args)
        for (int i = 1; i < args.length; i++) {
            if (args[i].equals("any")) any = true;
            else if (args[i].equals("range")) { lo = Long.decode(args[++i]); hi = Long.decode(args[++i]); }
            else want.add(Long.decode(args[i]));
        }
        DecompInterface di = new DecompInterface();
        di.openProgram(currentProgram);
        int hits = 0;
        for (Function f : currentProgram.getFunctionManager().getFunctions(true)) {
            if (monitor.isCancelled() || hits >= 6) break;
            long ep = f.getEntryPoint().getOffset();
            if (ep < lo || ep > hi) continue;
            Set<Long> seen = new HashSet<>();
            for (Instruction ins : currentProgram.getListing().getInstructions(f.getBody(), true)) {
                if (!any && !ins.getMnemonicString().startsWith("CMP")) continue;
                for (int op = 0; op < ins.getNumOperands(); op++)
                    for (Object o : ins.getOpObjects(op))
                        if (o instanceof Scalar && want.contains(((Scalar) o).getUnsignedValue()))
                            seen.add(((Scalar) o).getUnsignedValue());
            }
            if (seen.containsAll(want)) {
                hits++;
                DecompileResults r = di.decompileFunction(f, 120, monitor);
                out.println("// ===== " + f.getName() + " @ " + f.getEntryPoint());
                out.println(r.decompileCompleted() ? r.getDecompiledFunction().getC() : "// failed: " + r.getErrorMessage());
            }
        }
        out.println("// " + hits + " functions");
        out.close();
    }
}
