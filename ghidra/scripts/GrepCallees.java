// Walks direct calls from a root function (breadth first, to a depth), decompiles each function
// reached and writes those whose C matches a regex, with the matching lines and the call path.
// usage (headless): -postScript GrepCallees.java <out.c> <depth> <root hex> <regex>
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.Function;
import java.io.FileWriter;
import java.io.PrintWriter;
import java.util.*;
import java.util.regex.Pattern;

public class GrepCallees extends GhidraScript {
    @Override
    public void run() throws Exception {
        String[] a = getScriptArgs();
        PrintWriter out = new PrintWriter(new FileWriter(a[0]));
        int depth = Integer.parseInt(a[1]);
        Function root = getFunctionContaining(toAddr(a[2]));
        Pattern pat = Pattern.compile(a[3]);
        DecompInterface di = new DecompInterface();
        di.openProgram(currentProgram);
        Map<Function, String> path = new LinkedHashMap<>();
        Deque<Function> q = new ArrayDeque<>();
        Map<Function, Integer> level = new HashMap<>();
        path.put(root, root.getName());
        level.put(root, 0);
        q.add(root);
        int hits = 0;
        while (!q.isEmpty()) {
            Function f = q.poll();
            DecompileResults r = di.decompileFunction(f, 60, monitor);
            if (r.decompileCompleted()) {
                String c = r.getDecompiledFunction().getC();
                StringBuilder lines = new StringBuilder();
                for (String line : c.split("\n"))
                    if (pat.matcher(line).find()) lines.append("//   ").append(line.trim()).append("\n");
                if (lines.length() > 0) {
                    hits++;
                    out.println("// ===== " + f.getName() + " @ " + f.getEntryPoint() + "  path: " + path.get(f));
                    out.print(lines);
                }
            }
            if (level.get(f) >= depth) continue;
            for (Function g : f.getCalledFunctions(monitor)) {
                if (path.containsKey(g) || g.isThunk() || g.isExternal()) continue;
                path.put(g, path.get(f) + " > " + g.getName());
                level.put(g, level.get(f) + 1);
                q.add(g);
            }
        }
        out.println("// " + hits + " of " + path.size() + " functions matched");
        out.close();
    }
}
