"""Lint gate (Code Master DD-01 item 4): pyflakes over brain/ and tools/, failing on the errors that crash a match at
run time (an undefined name or local, a name used before it is set, a duplicate argument, a syntax error) and not on
style (unused imports or variables, f-strings without fields). pyflakes is a developer tool (requirements-dev.txt);
it is not shipped and the mod never runs it.

usage: python -I test_lint.py
"""
import glob
import os
import sys
import tempfile

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
try:
    from pyflakes import checker, messages
except ImportError:
    raise SystemExit("FAIL: pyflakes is missing: python -m pip install -r requirements-dev.txt")
import ast  # noqa: E402

# the message kinds that are bugs, not style
FATAL = (messages.UndefinedName, messages.UndefinedLocal, messages.UndefinedExport, messages.DuplicateArgument,
         messages.ReturnOutsideFunction, messages.YieldOutsideFunction, messages.ContinueOutsideLoop,
         messages.BreakOutsideLoop, messages.DefaultExceptNotLast, messages.TwoStarredExpressions,
         messages.TooManyExpressionsInStarredAssignment, messages.ForwardAnnotationSyntaxError,
         messages.IsLiteral)


def problems(paths):
    """[(file, line, text)] of the fatal kinds, syntax errors included."""
    out = []
    for p in paths:
        src = open(p, encoding="utf-8-sig", errors="replace").read()   # (a BOM, as Python itself reads)
        try:
            tree = ast.parse(src, filename=p)
        except SyntaxError as e:
            out.append((p, e.lineno or 0, f"syntax error: {e.msg}"))
            continue
        for m in checker.Checker(tree, filename=p).messages:
            if isinstance(m, FATAL):
                out.append((p, m.lineno, m.message % m.message_args))
    return out


def main():
    # the gate catches what it is for (and leaves style alone)
    with tempfile.TemporaryDirectory() as tmp:
        bad, ok = os.path.join(tmp, "bad.py"), os.path.join(tmp, "ok.py")
        open(bad, "w").write("def f():\n    return undefined_thing\n")
        open(ok, "w").write("import os\n\ndef f():\n    x = 1\n    return f'plain'\n")
        assert [t for _, _, t in problems([bad])] == ["undefined name 'undefined_thing'"], problems([bad])
        assert problems([ok]) == [], problems([ok])
    files = sorted(glob.glob(os.path.join(ROOT, "brain", "*.py")) + glob.glob(os.path.join(ROOT, "tools", "*.py")))
    found = problems(files)
    for p, line, text in found:
        print(f"FAIL {os.path.relpath(p, ROOT)}:{line}: {text}")
    if found:
        raise SystemExit(1)
    print(f"lint OK ({len(files)} files: no undefined names, syntax errors or other run-time faults)")


if __name__ == "__main__":
    main()
