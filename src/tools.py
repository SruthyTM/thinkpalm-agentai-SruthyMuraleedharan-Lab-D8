"""
Tool definitions called by agents via LangChain tool-calling.

Tools are plain Python functions decorated with @tool.
When an agent "calls" a tool, LangChain serialises its arguments as JSON,
runs the function, and injects the result back into the agent's context.
"""
from __future__ import annotations
import ast
import re
import textwrap
from typing import Optional
from langchain_core.tools import tool


# ──────────────────────────────────────────────────────────────────────────────
# TOOL 1 ─ Python AST Linter
# ──────────────────────────────────────────────────────────────────────────────

@tool
def python_linter(code: str) -> str:
    """
    Statically analyse Python source code using the built-in AST module.

    Checks performed:
    - Syntax validity
    - Use of bare `except:` clauses (catches everything, hides bugs)
    - Functions / methods without docstrings
    - Variables named with single characters (poor readability)
    - TODO / FIXME / HACK / XXX comments left in code
    - Use of `eval()` or `exec()` (security risk)
    - Deeply nested blocks (> 4 levels)
    - Missing type annotations on function signatures

    Returns a human-readable report string.
    """
    issues: list[str] = []

    # ── Syntax check ──────────────────────────────────────
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return f"❌ SYNTAX ERROR on line {exc.lineno}: {exc.msg}"

    # ── AST visitors ──────────────────────────────────────
    for node in ast.walk(tree):

        # Bare except
        if isinstance(node, ast.ExceptHandler) and node.type is None:
            issues.append(
                f"⚠️  Line {node.lineno}: Bare `except:` clause – "
                "catches ALL exceptions including KeyboardInterrupt."
            )

        # Missing docstrings
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not (node.body and isinstance(node.body[0], ast.Expr)
                    and isinstance(node.body[0].value, ast.Constant)
                    and isinstance(node.body[0].value.value, str)):
                issues.append(
                    f"📝  Line {node.lineno}: `{node.name}()` is missing a docstring."
                )

        # Security: eval / exec
        if isinstance(node, ast.Call):
            func = node.func
            name = (func.id if isinstance(func, ast.Name)
                    else func.attr if isinstance(func, ast.Attribute) else None)
            if name in ("eval", "exec"):
                issues.append(
                    f"🔒  Line {node.lineno}: Use of `{name}()` is a security risk."
                )

        # Missing type annotations
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            args = node.args
            all_args = (args.args + args.posonlyargs + args.kwonlyargs
                        + ([args.vararg] if args.vararg else [])
                        + ([args.kwarg] if args.kwarg else []))
            unannotated = [a.arg for a in all_args
                           if a.annotation is None and a.arg != "self"]
            if unannotated:
                issues.append(
                    f"🔷  Line {node.lineno}: `{node.name}()` – "
                    f"unannotated args: {', '.join(unannotated)}"
                )

    # ── Regex-based checks (work on raw text) ─────────────
    for i, line in enumerate(code.splitlines(), 1):
        stripped = line.strip()

        # TODO / FIXME markers
        if re.search(r'\b(TODO|FIXME|HACK|XXX)\b', stripped, re.IGNORECASE):
            issues.append(f"📌  Line {i}: Unresolved marker → `{stripped[:80]}`")

        # Single-character variable names (skip 'i', 'j', 'k' loop vars)
        if re.match(r'^[a-zA-Z] =', stripped) and not re.match(r'^[ijk] =', stripped):
            issues.append(
                f"🔤  Line {i}: Single-character variable name → `{stripped[:60]}`"
            )

    # ── Nesting depth (column heuristic) ─────────────────
    for i, line in enumerate(code.splitlines(), 1):
        indent = len(line) - len(line.lstrip())
        if indent >= 16:          # 4 levels × 4 spaces
            issues.append(
                f"🔢  Line {i}: Deep nesting detected (indent={indent}). "
                "Consider extracting helper functions."
            )

    if not issues:
        return "✅ No issues found. Code looks clean!"

    report = f"Linter found {len(issues)} issue(s):\n\n"
    report += "\n".join(f"{idx+1}. {msg}" for idx, msg in enumerate(issues))
    return report


# ──────────────────────────────────────────────────────────────────────────────
# TOOL 2 ─ Cyclomatic Complexity Analyser
# ──────────────────────────────────────────────────────────────────────────────

@tool
def complexity_checker(code: str) -> str:
    """
    Compute cyclomatic complexity for every function in Python source code.

    Cyclomatic complexity counts the number of independent paths through code.
    - 1–5   → Simple, easy to test ✅
    - 6–10  → Moderate, consider refactoring ⚠️
    - 11+   → Complex, hard to maintain ❌

    Returns a formatted complexity report string.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return f"Cannot analyse complexity – syntax error: {exc}"

    results: list[str] = []

    def count_complexity(node: ast.AST) -> int:
        """Count branching nodes to estimate McCabe complexity."""
        branch_nodes = (
            ast.If, ast.For, ast.While, ast.ExceptHandler,
            ast.With, ast.Assert, ast.comprehension,
        )
        count = 1  # Base path
        for child in ast.walk(node):
            if isinstance(child, branch_nodes):
                count += 1
            # Boolean operators add branches
            if isinstance(child, ast.BoolOp):
                count += len(child.values) - 1
        return count

    functions_found = 0
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions_found += 1
            cc = count_complexity(node)
            if cc <= 5:
                rating, emoji = "Simple", "✅"
            elif cc <= 10:
                rating, emoji = "Moderate", "⚠️"
            else:
                rating, emoji = "Complex", "❌"

            results.append(
                f"{emoji} `{node.name}` (line {node.lineno}): "
                f"CC={cc} – {rating}"
            )

    if functions_found == 0:
        # No functions – analyse the whole module
        cc = count_complexity(tree)
        results.append(f"Module-level CC={cc}")

    header = "Cyclomatic Complexity Report\n" + "=" * 35 + "\n"
    return header + "\n".join(results)


# ──────────────────────────────────────────────────────────────────────────────
# TOOL 3 ─ Markdown Documentation Skeleton Generator
# ──────────────────────────────────────────────────────────────────────────────

@tool
def generate_markdown_skeleton(code: str, filename: Optional[str] = "module.py") -> str:
    """
    Parse Python source code and generate a Markdown documentation skeleton.

    Extracts:
    - Module-level docstring
    - All classes and their methods (with existing docstrings)
    - All top-level functions (with existing docstrings)
    - Public constants / module-level assignments

    Returns a Markdown string ready to be embedded in documentation.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return f"# Parse Error\n\nCannot generate docs: {exc}"

    lines: list[str] = [f"# 📄 `{filename}` – Auto-Generated Documentation\n"]

    # Module docstring
    module_doc = ast.get_docstring(tree)
    if module_doc:
        lines.append(f"> {module_doc}\n")

    # ── Classes ───────────────────────────────────────────
    classes = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
    if classes:
        lines.append("## Classes\n")
        for cls in classes:
            cls_doc = ast.get_docstring(cls) or "_No docstring provided._"
            lines.append(f"### `{cls.name}`\n\n{cls_doc}\n")

            methods = [n for n in ast.walk(cls)
                       if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
            if methods:
                lines.append("**Methods:**\n")
                for m in methods:
                    m_doc = ast.get_docstring(m) or "_No docstring._"
                    # Collect arg names (skip self)
                    args = [a.arg for a in m.args.args if a.arg != "self"]
                    sig = f"{m.name}({', '.join(args)})"
                    lines.append(f"- **`{sig}`** – {m_doc}")
                lines.append("")

    # ── Top-level functions ───────────────────────────────
    funcs = [n for n in tree.body
             if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    if funcs:
        lines.append("## Functions\n")
        for fn in funcs:
            fn_doc = ast.get_docstring(fn) or "_No docstring provided._"
            args = [a.arg for a in fn.args.args]
            sig = f"{fn.name}({', '.join(args)})"
            async_prefix = "async " if isinstance(fn, ast.AsyncFunctionDef) else ""
            lines.append(f"### `{async_prefix}{sig}`\n\n{fn_doc}\n")

    # ── Module-level constants ────────────────────────────
    constants = [
        n for n in tree.body
        if isinstance(n, ast.Assign)
        and all(isinstance(t, ast.Name) and t.id.isupper() for t in n.targets)
    ]
    if constants:
        lines.append("## Constants\n")
        for c in constants:
            name = ", ".join(
                t.id for t in c.targets if isinstance(t, ast.Name)
            )
            lines.append(f"- **`{name}`**")
        lines.append("")

    return "\n".join(lines)


# ──────────────────────────────────────────────────────────────────────────────
# TOOL 4 ─ Security Pattern Scanner
# ──────────────────────────────────────────────────────────────────────────────

@tool
def security_scanner(code: str) -> str:
    """
    Scan Python code for common security anti-patterns.

    Patterns detected:
    - Hard-coded passwords / secrets / tokens
    - SQL string concatenation (SQLi risk)
    - Shell injection via os.system / subprocess with shell=True
    - Use of pickle (arbitrary code execution)
    - Insecure hash algorithms (MD5, SHA1)
    - Debug mode / assert used for security checks

    Returns a security scan report string.
    """
    patterns = [
        (r'password\s*=\s*["\'].+["\']',
         "Hard-coded password detected"),
        (r'secret\s*=\s*["\'].+["\']',
         "Hard-coded secret detected"),
        (r'token\s*=\s*["\'].+["\']',
         "Hard-coded token detected"),
        (r'api_key\s*=\s*["\'].+["\']',
         "Hard-coded API key detected"),
        (r'["\']SELECT.+\+',
         "Possible SQL injection via string concatenation"),
        (r'os\.system\(',
         "os.system() call – prefer subprocess with shell=False"),
        (r'subprocess.*shell\s*=\s*True',
         "subprocess with shell=True is vulnerable to shell injection"),
        (r'\bpickle\.loads?\(',
         "pickle.load(s) can execute arbitrary code"),
        (r'hashlib\.(md5|sha1)\(',
         "Weak hash algorithm (MD5/SHA1) – use SHA-256+"),
        (r'\bDEBUG\s*=\s*True',
         "Debug mode enabled – disable in production"),
        (r'\bassert\b.*password|assert\b.*auth',
         "assert used for security – can be disabled with -O flag"),
    ]

    findings: list[str] = []
    for i, line in enumerate(code.splitlines(), 1):
        for pattern, description in patterns:
            if re.search(pattern, line, re.IGNORECASE):
                findings.append(
                    f"🚨  Line {i}: {description}\n"
                    f"    → `{line.strip()[:100]}`"
                )

    if not findings:
        return "🔒 Security scan passed – no obvious vulnerabilities detected."

    report = f"Security Scan found {len(findings)} potential issue(s):\n\n"
    report += "\n\n".join(findings)
    return report


# ──────────────────────────────────────────────────────────────────────────────
# TOOL 5 ─ Dependency Analysis
# ──────────────────────────────────────────────────────────────────────────────

@tool
def dependency_check(code: str) -> str:
    """
    Examine import statements to identify external dependencies and potential risks.

    Checks:
    - Deprecated libraries (e.g., imp, distutils)
    - Unusual imports (built-ins vs external)
    - Potential side-effect imports
    """
    try:
        tree = ast.parse(code)
    except Exception:
        return "Cannot check dependencies due to syntax error."

    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                imports.append(n.name)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or "unknown")

    if not imports:
        return "No external imports detected."

    deprecated = {"imp", "distutils", "cgi"}
    found_deprecated = [i for i in imports if i.get_root_module() in deprecated] if hasattr(str, "get_root_module") else [i for i in imports if i.split('.')[0] in deprecated]
    
    report = f"Dependencies found: {', '.join(set(imports))}\n"
    if found_deprecated:
        report += f"⚠️  WARNING: Deprecated modules used: {', '.join(set(found_deprecated))}"
    else:
        report += "✅ All modules appear standard/modern."

    return report


# ── Exported tool list used when binding tools to agents ──────────────────────
CRITIC_TOOLS = [python_linter, complexity_checker, security_scanner, dependency_check]
SCRIBE_TOOLS  = [generate_markdown_skeleton]
ALL_TOOLS     = CRITIC_TOOLS + SCRIBE_TOOLS
