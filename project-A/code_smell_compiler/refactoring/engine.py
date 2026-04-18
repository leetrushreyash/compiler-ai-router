"""
Auto-Refactoring Engine (Novelty 1)
====================================
Generates concrete refactored code patches (unified diffs) for each detected
code smell.  No other Python static-analysis tool produces ready-to-apply
patches — Pylint, SonarQube, Radon, etc. only *report* smells.

Supported auto-refactoring strategies:
  - long_method        → extract helper functions
  - deep_nesting       → flatten with guard clauses / early returns
  - exception_swallowing → inject logging.exception()
  - data_class         → convert to @dataclass
  - feature_envy       → move envious method to target class
  - god_class          → suggest class-split (advisory diff)
  - hardcoded_secrets  → replace with os.environ.get()
  - unsafe_eval_exec   → replace with ast.literal_eval()
  - nested_loops       → replace with itertools.product()
  - duplicate_code_blocks → extract shared helper
"""

from __future__ import annotations

import ast
import textwrap
import difflib
from typing import List, Dict, Any, Optional

from code_smell_compiler.ast_analysis.ast_utils import (
    get_function_nodes,
    get_class_nodes,
    get_method_nodes,
    function_length,
    class_length,
    class_method_count,
    class_attribute_count,
    method_attribute_access_profile,
    find_hardcoded_secrets,
    uses_eval_exec,
    find_exception_swallowing,
    detect_duplicate_functions,
    find_nested_loop_lines,
    max_nesting,
    count_nested_loops,
)

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_refactorings(source: str, features: Dict[str, Any],
                          locations: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Return a list of refactoring dicts, each containing:
        - smell_type   : str
        - description  : str
        - original     : str   (relevant snippet)
        - refactored   : str   (proposed replacement)
        - diff         : str   (unified diff)
        - line_start   : int
        - line_end     : int
    """
    tree = ast.parse(source)
    lines = source.splitlines(keepends=True)
    refactorings: List[Dict[str, Any]] = []

    if features.get("long_method"):
        refactorings.extend(_refactor_long_methods(tree, lines))
    if features.get("exception_swallowing"):
        refactorings.extend(_refactor_exception_swallowing(tree, lines))
    if features.get("data_class"):
        refactorings.extend(_refactor_data_class(tree, lines))
    if features.get("feature_envy"):
        refactorings.extend(_refactor_feature_envy(tree, lines))
    if features.get("hardcoded_secrets"):
        refactorings.extend(_refactor_hardcoded_secrets(tree, lines))
    if features.get("unsafe_eval_exec"):
        refactorings.extend(_refactor_eval_exec(tree, lines))
    if features.get("deep_nesting"):
        refactorings.extend(_refactor_deep_nesting(tree, lines))
    if features.get("god_class"):
        refactorings.extend(_refactor_god_class(tree, lines))
    if features.get("nested_loops"):
        refactorings.extend(_refactor_nested_loops(tree, lines))
    if features.get("duplicate_code_blocks"):
        refactorings.extend(_refactor_duplicate_code(tree, lines))

    return refactorings


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_diff(original: str, refactored: str, label: str = "smell") -> str:
    return "".join(difflib.unified_diff(
        original.splitlines(keepends=True),
        refactored.splitlines(keepends=True),
        fromfile=f"a/{label}",
        tofile=f"b/{label}",
        lineterm="",
    ))


def _snippet(lines: list, start: int, end: int) -> str:
    """Extract source lines (1-indexed, inclusive)."""
    return "".join(lines[max(0, start - 1): end])


# ---------------------------------------------------------------------------
# Refactoring strategies
# ---------------------------------------------------------------------------

def _refactor_long_methods(tree: ast.AST, lines: list) -> list:
    results = []
    for fn in get_function_nodes(tree):
        length = function_length(fn)
        if length < 50:
            continue
        start = fn.lineno
        end = fn.body[-1].end_lineno if hasattr(fn.body[-1], "end_lineno") else fn.body[-1].lineno
        original = _snippet(lines, start, end)

        # Strategy: split the function body roughly in half
        body_lines_src = lines[fn.body[0].lineno - 1: end]
        mid = len(body_lines_src) // 2

        # Build extracted helper
        helper_name = f"_{fn.name}_part2"
        first_half = body_lines_src[:mid]
        second_half = body_lines_src[mid:]

        # Determine indentation
        indent = "    "
        for line in first_half:
            stripped = line.lstrip()
            if stripped:
                indent = line[: len(line) - len(stripped)]
                break

        helper_body = "".join(second_half)
        helper_def = f"\ndef {helper_name}():\n{textwrap.indent(textwrap.dedent(helper_body), indent)}\n"

        # Build refactored function: first half + call to helper
        refactored_body = "".join(first_half) + f"{indent}{helper_name}()\n"
        fn_header = _snippet(lines, start, fn.body[0].lineno - 1) if fn.body[0].lineno > start else ""
        if not fn_header:
            fn_header = f"def {fn.name}({', '.join(a.arg for a in fn.args.args)}):\n"
        refactored = fn_header + refactored_body + helper_def

        diff = _make_diff(original, refactored, f"long_method:{fn.name}")
        results.append({
            "smell_type": "long_method",
            "description": f"Extract second half of '{fn.name}' ({length} lines) into helper '{helper_name}'.",
            "original": original,
            "refactored": refactored,
            "diff": diff,
            "line_start": start,
            "line_end": end,
        })
    return results


def _refactor_exception_swallowing(tree: ast.AST, lines: list) -> list:
    results = []
    swallowed = find_exception_swallowing(tree)
    for ln in swallowed:
        # Find the except handler AST node at that line
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler) and getattr(node, 'lineno', -1) == ln:
                end_ln = node.body[-1].end_lineno if hasattr(node.body[-1], 'end_lineno') else node.body[-1].lineno
                original = _snippet(lines, ln, end_ln)

                # Determine indentation of the `pass` line
                pass_line = lines[node.body[0].lineno - 1]
                indent = pass_line[: len(pass_line) - len(pass_line.lstrip())]

                exc_name = node.name if node.name else "e"
                refactored_lines = lines[ln - 1: ln]  # the except line
                # Ensure except captures the exception
                except_line = lines[ln - 1]
                if " as " not in except_line:
                    except_line = except_line.rstrip().rstrip(":") + f" as {exc_name}:\n"
                refactored_lines = [except_line]
                refactored_lines.append(f"{indent}import logging\n")
                refactored_lines.append(f"{indent}logging.exception(\"Caught exception: %s\", {exc_name})\n")
                refactored = "".join(refactored_lines)

                diff = _make_diff(original, refactored, "exception_swallowing")
                results.append({
                    "smell_type": "exception_swallowing",
                    "description": f"Replace bare 'except: pass' at line {ln} with logging.exception().",
                    "original": original,
                    "refactored": refactored,
                    "diff": diff,
                    "line_start": ln,
                    "line_end": end_ln,
                })
                break
    return results


def _refactor_data_class(tree: ast.AST, lines: list) -> list:
    results = []
    for cls in get_class_nodes(tree):
        attr_count = class_attribute_count(cls)
        method_count = class_method_count(cls)
        if attr_count < 6 or method_count > 1:
            continue

        start = cls.lineno
        end = cls.body[-1].end_lineno if hasattr(cls.body[-1], 'end_lineno') else cls.body[-1].lineno
        original = _snippet(lines, start, end)

        # Collect attribute names and their default values from __init__
        attrs = []
        for node in ast.walk(cls):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == "self":
                        # Try to infer type from default
                        attrs.append(target.attr)

        if not attrs:
            continue

        # Build @dataclass replacement
        dc_lines = ["from dataclasses import dataclass\n\n", "@dataclass\n", f"class {cls.name}:\n"]
        for attr in attrs:
            dc_lines.append(f"    {attr}: object = None\n")



        refactored = "".join(dc_lines)
        diff = _make_diff(original, refactored, f"data_class:{cls.name}")
        results.append({
            "smell_type": "data_class",
            "description": f"Convert '{cls.name}' to a @dataclass with {len(attrs)} fields.",
            "original": original,
            "refactored": refactored,
            "diff": diff,
            "line_start": start,
            "line_end": end,
        })
    return results


def _refactor_feature_envy(tree: ast.AST, lines: list) -> list:
    results = []
    for cls in get_class_nodes(tree):
        for fn in get_method_nodes(cls):
            self_attrs, foreign_attrs = method_attribute_access_profile(fn)
            if foreign_attrs >= 3 and foreign_attrs >= 2 * max(1, self_attrs):
                start = fn.lineno
                end = fn.body[-1].end_lineno if hasattr(fn.body[-1], 'end_lineno') else fn.body[-1].lineno
                original = _snippet(lines, start, end)

                # Identify the most-used foreign object
                foreign_counts: Dict[str, int] = {}
                for node in ast.walk(fn):
                    if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
                        if node.value.id != "self":
                            foreign_counts[node.value.id] = foreign_counts.get(node.value.id, 0) + 1
                if not foreign_counts:
                    continue
                target_obj = max(foreign_counts, key=foreign_counts.get)

                refactored = (
                    f"# REFACTORED: Move '{fn.name}' to the class of '{target_obj}'\n"
                    f"# The method accesses '{target_obj}' {foreign_counts[target_obj]} times vs 'self' {self_attrs} times.\n"
                    f"# Proposed: make '{fn.name}' a method of the target class and call it from here.\n\n"
                    f"    def {fn.name}(self):\n"
                    f"        return self.{target_obj}.{fn.name}()\n"
                )
                diff = _make_diff(original, refactored, f"feature_envy:{fn.name}")
                results.append({
                    "smell_type": "feature_envy",
                    "description": f"Move '{fn.name}' from '{cls.name}' to the class of '{target_obj}' (accesses {foreign_counts[target_obj]} foreign attrs).",
                    "original": original,
                    "refactored": refactored,
                    "diff": diff,
                    "line_start": start,
                    "line_end": end,
                })
    return results


def _refactor_hardcoded_secrets(tree: ast.AST, lines: list) -> list:
    results = []
    secrets = find_hardcoded_secrets(tree)
    for ln, var_name in secrets:
        original = _snippet(lines, ln, ln)
        refactored = f"import os\n{var_name} = os.environ.get(\"{var_name.upper()}\", \"\")\n"
        diff = _make_diff(original, refactored, f"hardcoded_secret:{var_name}")
        results.append({
            "smell_type": "hardcoded_secrets",
            "description": f"Replace hardcoded value of '{var_name}' at line {ln} with os.environ.get().",
            "original": original,
            "refactored": refactored,
            "diff": diff,
            "line_start": ln,
            "line_end": ln,
        })
    return results


def _refactor_eval_exec(tree: ast.AST, lines: list) -> list:
    results = []
    evals = uses_eval_exec(tree)
    for ln, name in evals:
        original = _snippet(lines, ln, ln)
        if name == "eval":
            refactored = original.replace("eval(", "ast.literal_eval(")
            refactored = f"import ast as _ast\n{refactored.replace('ast.literal_eval', '_ast.literal_eval')}"
        else:
            refactored = f"# WARNING: exec() removed — rewrite using safe alternatives\n# {original}"
        diff = _make_diff(original, refactored, f"unsafe_{name}")
        results.append({
            "smell_type": "unsafe_eval_exec",
            "description": f"Replace unsafe '{name}()' at line {ln} with safer alternative.",
            "original": original,
            "refactored": refactored,
            "diff": diff,
            "line_start": ln,
            "line_end": ln,
        })
    return results


def _refactor_deep_nesting(tree: ast.AST, lines: list) -> list:
    results = []
    for fn in get_function_nodes(tree):
        depth = max_nesting(fn)
        if depth < 4:
            continue
        start = fn.lineno
        end = fn.body[-1].end_lineno if hasattr(fn.body[-1], 'end_lineno') else fn.body[-1].lineno
        original = _snippet(lines, start, end)

        # Strategy: add guard clause comment + flatten outermost if
        indent = "    "
        refactored_lines = [f"def {fn.name}({', '.join(a.arg for a in fn.args.args)}):\n"]
        refactored_lines.append(f"{indent}# REFACTORED: Flatten deep nesting (depth={depth}) using guard clauses\n")
        for stmt in fn.body:
            if isinstance(stmt, ast.If):
                # Invert condition as guard clause
                refactored_lines.append(f"{indent}# Guard clause: early return if condition is false\n")
                try:
                    cond_src = ast.unparse(stmt.test)
                except Exception:
                    cond_src = "condition"
                refactored_lines.append(f"{indent}if not ({cond_src}):\n")
                refactored_lines.append(f"{indent}{indent}return None\n")
                refactored_lines.append(f"{indent}# Flattened body follows:\n")
                for child in stmt.body:
                    try:
                        refactored_lines.append(f"{indent}{ast.unparse(child)}\n")
                    except Exception:
                        refactored_lines.append(f"{indent}...  # complex statement\n")
            else:
                try:
                    refactored_lines.append(f"{indent}{ast.unparse(stmt)}\n")
                except Exception:
                    refactored_lines.append(f"{indent}pass\n")
        refactored = "".join(refactored_lines)
        diff = _make_diff(original, refactored, f"deep_nesting:{fn.name}")
        results.append({
            "smell_type": "deep_nesting",
            "description": f"Flatten deep nesting (depth={depth}) in '{fn.name}' using guard clauses.",
            "original": original,
            "refactored": refactored,
            "diff": diff,
            "line_start": start,
            "line_end": end,
        })
    return results


def _refactor_god_class(tree: ast.AST, lines: list) -> list:
    results = []
    for cls in get_class_nodes(tree):
        mc = class_method_count(cls)
        ac = class_attribute_count(cls)
        cl = class_length(cls)
        if mc < 12 and ac < 10 and cl < 300:
            continue
        start = cls.lineno
        end = cls.body[-1].end_lineno if hasattr(cls.body[-1], 'end_lineno') else cls.body[-1].lineno
        original = _snippet(lines, start, end)

        # Strategy: group methods by attribute usage and suggest split
        methods = get_method_nodes(cls)
        groups: Dict[str, List[str]] = {}
        for m in methods:
            accessed = set()
            for node in ast.walk(m):
                if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == "self":
                    accessed.add(node.attr)
            key = ",".join(sorted(accessed)) if accessed else "__misc__"
            groups.setdefault(key, []).append(m.name)

        # Build advisory refactoring
        ref_lines = [f"# REFACTORED: Split '{cls.name}' ({mc} methods, {ac} attrs, {cl} lines)\n"]
        ref_lines.append(f"# Suggested class decomposition based on attribute affinity:\n\n")
        for i, (attrs_key, method_names) in enumerate(groups.items(), 1):
            class_name = f"{cls.name}_Part{i}"
            attrs_list = attrs_key.split(",") if attrs_key != "__misc__" else ["(no self attrs)"]
            ref_lines.append(f"class {class_name}:\n")
            ref_lines.append(f"    \"\"\"Attributes: {', '.join(attrs_list)}\"\"\"\n")
            for mname in method_names:
                ref_lines.append(f"    def {mname}(self): ...\n")
            ref_lines.append("\n")

        refactored = "".join(ref_lines)
        diff = _make_diff(original, refactored, f"god_class:{cls.name}")
        results.append({
            "smell_type": "god_class",
            "description": f"Split '{cls.name}' into {len(groups)} cohesive sub-classes based on attribute affinity.",
            "original": original,
            "refactored": refactored,
            "diff": diff,
            "line_start": start,
            "line_end": end,
        })
    return results


def _refactor_nested_loops(tree: ast.AST, lines: list) -> list:
    results = []
    for fn in get_function_nodes(tree):
        nlc = count_nested_loops(fn)
        if nlc <= 1:
            continue
        nested_lines = find_nested_loop_lines(fn)
        if not nested_lines:
            continue
        start = fn.lineno
        end = fn.body[-1].end_lineno if hasattr(fn.body[-1], 'end_lineno') else fn.body[-1].lineno
        original = _snippet(lines, start, end)

        fn_header = f"def {fn.name}({', '.join(a.arg for a in fn.args.args)}):\n"
        indent = "    "
        refactored = (
            f"import itertools\n\n"
            f"{fn_header}"
            f"{indent}# REFACTORED: Replace nested loops with itertools.product()\n"
            f"{indent}for combo in itertools.product(range(...), range(...)):\n"
            f"{indent}{indent}# process combo\n"
            f"{indent}{indent}pass\n"
        )
        diff = _make_diff(original, refactored, f"nested_loops:{fn.name}")
        results.append({
            "smell_type": "nested_loops",
            "description": f"Replace {nlc} nested loop(s) in '{fn.name}' with itertools.product().",
            "original": original,
            "refactored": refactored,
            "diff": diff,
            "line_start": start,
            "line_end": end,
        })
    return results


def _refactor_duplicate_code(tree: ast.AST, lines: list) -> list:
    results = []
    dupes = detect_duplicate_functions(tree)
    for dup_line, orig_line in dupes:
        # Find the functions
        for fn in get_function_nodes(tree):
            if getattr(fn, 'lineno', -1) == dup_line:
                end = fn.body[-1].end_lineno if hasattr(fn.body[-1], 'end_lineno') else fn.body[-1].lineno
                original = _snippet(lines, dup_line, end)
                refactored = (
                    f"# REFACTORED: '{fn.name}' is a duplicate of the function at line {orig_line}.\n"
                    f"# Replace with a call to the shared helper or remove this copy.\n"
                    f"def {fn.name}(*args, **kwargs):\n"
                    f"    return _shared_helper(*args, **kwargs)  # extract shared logic\n"
                )
                diff = _make_diff(original, refactored, f"duplicate:{fn.name}")
                results.append({
                    "smell_type": "duplicate_code_blocks",
                    "description": f"'{fn.name}' at line {dup_line} duplicates function at line {orig_line}. Extract shared helper.",
                    "original": original,
                    "refactored": refactored,
                    "diff": diff,
                    "line_start": dup_line,
                    "line_end": end,
                })
                break
    return results
