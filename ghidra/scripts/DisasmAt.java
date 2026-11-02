// Disassembles a few instructions before and after each address, with the containing function.
// usage (headless): -postScript DisasmAt.java <out.txt> <hex addr> [<hex addr> ...]   (appends)
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.Instruction;
import java.io.FileWriter;
import java.io.PrintWriter;

public class DisasmAt extends GhidraScript {
    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        PrintWriter out = new PrintWriter(new FileWriter(args[0], true));
        for (int i = 1; i < args.length; i++) {
            Address a = toAddr(args[i]);
            Function f = getFunctionContaining(a);
            out.println("== " + currentProgram.getName() + " " + args[i] + " in " + (f == null ? "?" : f.getName() + " @ " + f.getEntryPoint()));
            Instruction ins = getInstructionAt(a);
            if (ins == null) ins = getInstructionContaining(a);
            if (ins == null) { out.println("   no instruction"); continue; }
            Instruction p = ins;
            for (int k = 0; k < 6 && p.getPrevious() != null; k++) p = p.getPrevious();
            for (int k = 0; k < 16 && p != null; k++, p = p.getNext())
                out.println((p.getAddress().equals(a) ? " > " : "   ") + p.getAddress() + "  " + p);
        }
        out.close();
    }
}
