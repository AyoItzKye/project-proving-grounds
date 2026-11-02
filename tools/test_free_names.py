"""No name is read that nothing binds (the brain died at its start on `TEST_MODE`, a name live_bots never had, since
302088e; no test ran its main). Every brain and tools file is parsed: a name read (not an attribute) that no
assignment, import, def, class, parameter, loop, with, except or global in the same file binds, and that is no builtin,
is a NameError waiting for its line. Crude on purpose (no scopes): it misses a name bound only elsewhere in the file,
never reports a real one wrongly.

usage: python -I test_free_names.py      -> "free names OK (... files)"
"""
import ast
import builtins
import glob
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def free_names(path):
    tree = ast.parse(open(path, encoding="utf-8-sig").read(), path)
    bound = set(dir(builtins)) | {"__file__", "__name__", "__doc__"}
    for n in ast.walk(tree):
        if isinstance(n, ast.Name) and isinstance(n.ctx, (ast.Store, ast.Del)):
            bound.add(n.id)
        elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            bound.add(n.name)
        elif isinstance(n, ast.arg):
            bound.add(n.arg)
        elif isinstance(n, (ast.Import, ast.ImportFrom)):
            bound |= {(a.asname or a.name).split(".")[0] for a in n.names}
        elif isinstance(n, ast.ExceptHandler) and n.name:
            bound.add(n.name)
        elif isinstance(n, (ast.Global, ast.Nonlocal)):
            bound |= set(n.names)
    return sorted({(n.id, n.lineno) for n in ast.walk(tree)
                   if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load) and n.id not in bound}, key=lambda x: x[1])


def main():
    files = sorted(glob.glob(os.path.join(HERE, "..", "brain", "*.py")) + glob.glob(os.path.join(HERE, "*.py")))
    fails = [f"{os.path.relpath(p, os.path.join(HERE, '..'))}: {name} line {line}"
             for p in files for name, line in free_names(p)]
    # the check itself: the bug of is one
    bad = os.path.join(HERE, "..", "logs", "tmp", "_free_names_case.py")
    os.makedirs(os.path.dirname(bad), exist_ok=True)
    open(bad, "w", encoding="utf-8").write("import brain.bot\n\ndef main():\n    if TEST_MODE:\n        return 1\n")
    try:
        if free_names(bad) != [("TEST_MODE", 4)]:
            fails.append(f"the check missed the Oct 31 bug (found {free_names(bad)})")
    finally:
        os.remove(bad)
    if fails:
        print("\n".join(fails))
        sys.exit(1)
    print(f"free names OK ({len(files)} files)")


if __name__ == "__main__":
    main()
