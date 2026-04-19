"""Auto-fix engine — generate refactored code for detected code smells."""
import re
from typing import Dict, List, Any, Optional, Tuple


class AutoFixer:
    """Generate automatic fix suggestions and refactored code snippets."""

    def __init__(self):
        self.fixers = {
            "hardcoded_secrets": self._fix_hardcoded_secret,
            "sql_injection_risk": self._fix_sql_injection,
            "unsafe_deserialization": self._fix_unsafe_deserialization,
            "command_injection": self._fix_command_injection,
            "weak_crypto": self._fix_weak_crypto,
            "null_pointer_risk": self._fix_null_pointer,
            "dead_code": self._fix_dead_code,
            "long_method": self._fix_long_method,
            "god_object": self._fix_god_object,
            "deep_nesting": self._fix_deep_nesting,
            "unused_variables": self._fix_unused_variables,
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def suggest_fix(self, issue: Dict[str, Any], code: str = "") -> Dict[str, Any]:
        """Generate a fix suggestion for a detected issue.

        Args:
            issue: Detection result dict (must include 'type' and 'code')
            code: Full source code (optional, for context)

        Returns:
            Dict with original_code, fixed_code, explanation, and imports_needed
        """
        smell_type = issue.get("type", "")
        fixer = self.fixers.get(smell_type)

        if fixer is None:
            return {
                "smell_type": smell_type,
                "original_code": issue.get("code", ""),
                "fixed_code": None,
                "explanation": f"No auto-fix available for '{smell_type}'.",
                "imports_needed": [],
            }

        return fixer(issue, code)

    def suggest_fixes_for_file(
        self, issues: List[Dict[str, Any]], code: str
    ) -> List[Dict[str, Any]]:
        """Generate fix suggestions for all issues in a file.

        Args:
            issues: List of detected issues
            code: Full source code

        Returns:
            List of fix suggestions
        """
        return [self.suggest_fix(issue, code) for issue in issues]

    def apply_fixes(self, code: str, fixes: List[Dict[str, Any]]) -> str:
        """Apply auto-fixes to source code (simple line-based replacement).

        Processes fixes from bottom to top (by line number) so that
        earlier replacements don't shift line numbers.

        Args:
            code: Original source code
            fixes: List of fix dicts from suggest_fix()

        Returns:
            Refactored source code
        """
        lines = code.split("\n")

        # Sort by line number descending so replacements don't shift indices
        sorted_fixes = sorted(
            [f for f in fixes if f.get("fixed_code") and f.get("line")],
            key=lambda f: f.get("line", 0),
            reverse=True,
        )

        for fix in sorted_fixes:
            line_idx = fix["line"] - 1
            if 0 <= line_idx < len(lines):
                original = fix.get("original_code", "").strip()
                if original and original in lines[line_idx]:
                    indent = len(lines[line_idx]) - len(lines[line_idx].lstrip())
                    fixed_lines = fix["fixed_code"].split("\n")
                    indented = [" " * indent + fl for fl in fixed_lines]
                    lines[line_idx] = "\n".join(indented)

        # Collect any needed imports
        all_imports = set()
        for fix in fixes:
            for imp in fix.get("imports_needed", []):
                all_imports.add(imp)

        result = "\n".join(lines)
        if all_imports:
            import_block = "\n".join(sorted(all_imports))
            result = import_block + "\n\n" + result

        return result

    def generate_fixed_code(self, source_code: str, issues: List[Dict[str, Any]]) -> str:
        """Generate a corrected full-code output from issue detections.

        Falls back to the original source code if any unexpected error occurs.
        """
        if not source_code:
            return source_code

        try:
            fixes = self.suggest_fixes_for_file(issues or [], source_code)
            return self.apply_fixes(source_code, fixes)
        except Exception:
            return source_code

    # ------------------------------------------------------------------
    # Individual fixers
    # ------------------------------------------------------------------
    def _fix_hardcoded_secret(
        self, issue: Dict[str, Any], code: str
    ) -> Dict[str, Any]:
        """Replace hardcoded secret with os.environ.get()."""
        snippet = issue.get("code", "")
        line = issue.get("line", 0)

        # Extract variable name
        match = re.match(r"(\w+)\s*=\s*['\"](.+?)['\"]", snippet.strip())
        if not match:
            return self._no_fix(issue, "Could not parse secret assignment")

        var_name = match.group(1)
        env_var_name = var_name.upper()

        fixed = f"{var_name} = os.environ.get('{env_var_name}')"

        return {
            "smell_type": "hardcoded_secrets",
            "line": line,
            "original_code": snippet.strip(),
            "fixed_code": fixed,
            "explanation": (
                f"Replaced hardcoded value of '{var_name}' with "
                f"os.environ.get('{env_var_name}'). Set the environment variable "
                f"{env_var_name} in your deployment configuration."
            ),
            "imports_needed": ["import os"],
        }

    def _fix_sql_injection(
        self, issue: Dict[str, Any], code: str
    ) -> Dict[str, Any]:
        """Replace string-concatenated SQL with parameterized query."""
        snippet = issue.get("code", "")
        line = issue.get("line", 0)

        # Try to detect the pattern
        # Pattern: "SELECT ... " + var
        concat_match = re.search(
            r'(["\'])(.+?)\1\s*\+\s*(\w+)', snippet
        )
        # Pattern: f"SELECT ... {var}"
        fstring_match = re.search(
            r'f["\'](.+?\{(\w+)\}.*?)["\']', snippet
        )
        # Pattern: "SELECT ... %s" % var
        percent_match = re.search(
            r'["\'](.+?%s.*?)["\']\s*%\s*(\w+)', snippet
        )
        # Pattern: .format(var)
        format_match = re.search(
            r'["\'](.+?\{\}.*?)["\']\.format\((\w+)', snippet
        )

        if concat_match:
            sql_part = concat_match.group(2).strip()
            var = concat_match.group(3)
            fixed_sql = sql_part.rstrip("= ").rstrip("'\"") + " = %s"
            fixed = f'cursor.execute("{fixed_sql}", ({var},))'
        elif fstring_match:
            sql_template = fstring_match.group(1)
            var = fstring_match.group(2)
            param_sql = re.sub(r'\{' + var + r'\}', '%s', sql_template)
            fixed = f'cursor.execute("{param_sql}", ({var},))'
        elif percent_match:
            sql_template = percent_match.group(1)
            var = percent_match.group(2)
            fixed = f'cursor.execute("{sql_template}", ({var},))'
        elif format_match:
            sql_template = format_match.group(1)
            var = format_match.group(2)
            param_sql = sql_template.replace("{}", "%s")
            fixed = f'cursor.execute("{param_sql}", ({var},))'
        else:
            return self._no_fix(
                issue,
                "Use parameterized queries: cursor.execute('SELECT * FROM t WHERE id = %s', (user_id,))",
            )

        return {
            "smell_type": "sql_injection_risk",
            "line": line,
            "original_code": snippet.strip(),
            "fixed_code": fixed,
            "explanation": (
                "Replaced dynamic SQL string construction with a parameterized "
                "query to prevent SQL injection. Parameters are passed separately "
                "so they are properly escaped by the database driver."
            ),
            "imports_needed": [],
        }

    def _fix_unsafe_deserialization(
        self, issue: Dict[str, Any], code: str
    ) -> Dict[str, Any]:
        """Replace unsafe deserialization with safe alternatives."""
        snippet = issue.get("code", "")
        line = issue.get("line", 0)

        if "pickle.loads" in snippet or "pickle.load" in snippet:
            fixed = snippet.replace("pickle.loads", "json.loads").replace(
                "pickle.load", "json.load"
            )
            explanation = (
                "Replaced pickle (arbitrary code execution risk) with json. "
                "If binary serialization is needed, use a safe format or "
                "restrict allowed classes via RestrictedUnpickler."
            )
            imports = ["import json"]
        elif "yaml.load" in snippet and "safe_load" not in snippet:
            fixed = snippet.replace("yaml.load", "yaml.safe_load")
            explanation = (
                "Replaced yaml.load() with yaml.safe_load() to prevent "
                "arbitrary Python object instantiation from YAML."
            )
            imports = []
        elif "eval(" in snippet:
            fixed = snippet.replace("eval(", "ast.literal_eval(")
            explanation = (
                "Replaced eval() with ast.literal_eval() which only allows "
                "Python literal structures (strings, numbers, lists, dicts)."
            )
            imports = ["import ast"]
        elif "exec(" in snippet:
            fixed = "# REMOVED: exec() call — review business logic and use safe alternatives"
            explanation = (
                "Removed exec() call. exec() allows arbitrary code execution. "
                "Refactor to use a safe approach (e.g., dispatch table, config file)."
            )
            imports = []
        else:
            return self._no_fix(
                issue,
                "Use safe deserialization: json.loads(), yaml.safe_load(), "
                "ast.literal_eval()",
            )

        return {
            "smell_type": "unsafe_deserialization",
            "line": line,
            "original_code": snippet.strip(),
            "fixed_code": fixed,
            "explanation": explanation,
            "imports_needed": imports,
        }

    def _fix_null_pointer(
        self, issue: Dict[str, Any], code: str
    ) -> Dict[str, Any]:
        """Wrap chained access in safe null checks."""
        snippet = issue.get("code", "")
        line = issue.get("line", 0)

        # Detect chained attribute/key access
        # e.g., obj.prop.method().value  →  add None check
        stripped = snippet.strip()

        # Simple approach: wrap in getattr chain or try/except
        if "." in stripped:
            parts = stripped.split("=", 1)
            if len(parts) == 2:
                var = parts[0].strip()
                expr = parts[1].strip()
                fixed = (
                    f"try:\n"
                    f"    {var} = {expr}\n"
                    f"except (AttributeError, TypeError, KeyError, IndexError):\n"
                    f"    {var} = None"
                )
            else:
                fixed = (
                    f"try:\n"
                    f"    {stripped}\n"
                    f"except (AttributeError, TypeError, KeyError, IndexError):\n"
                    f"    pass  # Handle None/missing gracefully"
                )
        elif "[" in stripped:
            parts = stripped.split("=", 1)
            if len(parts) == 2:
                var = parts[0].strip()
                expr = parts[1].strip()
                fixed = (
                    f"try:\n"
                    f"    {var} = {expr}\n"
                    f"except (KeyError, IndexError, TypeError):\n"
                    f"    {var} = None"
                )
            else:
                fixed = (
                    f"try:\n"
                    f"    {stripped}\n"
                    f"except (KeyError, IndexError, TypeError):\n"
                    f"    pass"
                )
        else:
            return self._no_fix(
                issue,
                "Add null/None checks before accessing attributes or keys.",
            )

        return {
            "smell_type": "null_pointer_risk",
            "line": line,
            "original_code": snippet.strip(),
            "fixed_code": fixed,
            "explanation": (
                "Wrapped chained access in try/except to handle potential "
                "None values, missing keys or index errors gracefully."
            ),
            "imports_needed": [],
        }

    def _fix_dead_code(
        self, issue: Dict[str, Any], code: str
    ) -> Dict[str, Any]:
        """Suggest removal of dead/unreachable code."""
        snippet = issue.get("code", "")
        line = issue.get("line", 0)

        return {
            "smell_type": "dead_code",
            "line": line,
            "original_code": snippet.strip(),
            "fixed_code": "# [REMOVED] Dead/unreachable code deleted",
            "explanation": (
                "This code is unreachable (after return/break/raise) or unused. "
                "Removing it improves readability and reduces maintenance burden."
            ),
            "imports_needed": [],
        }

    def _fix_command_injection(
        self, issue: Dict[str, Any], code: str
    ) -> Dict[str, Any]:
        snippet = issue.get("code", "")
        line = issue.get("line", 0)

        fixed = re.sub(r"os\.system\((.+)\)", r"subprocess.run([\1], check=True)", snippet.strip())
        if fixed == snippet.strip():
            fixed = "# REVIEW: replace shell-based command execution with validated argument list"

        return {
            "smell_type": "command_injection",
            "line": line,
            "original_code": snippet.strip(),
            "fixed_code": fixed,
            "explanation": "Replace shell command execution with subprocess argument lists and input validation.",
            "imports_needed": ["import subprocess"],
        }

    def _fix_weak_crypto(
        self, issue: Dict[str, Any], code: str
    ) -> Dict[str, Any]:
        snippet = issue.get("code", "")
        line = issue.get("line", 0)
        fixed = snippet.replace("hashlib.md5", "hashlib.sha256").replace("hashlib.sha1", "hashlib.sha256")

        if fixed == snippet:
            return self._no_fix(issue, "Use stronger hash algorithms such as hashlib.sha256.")

        return {
            "smell_type": "weak_crypto",
            "line": line,
            "original_code": snippet.strip(),
            "fixed_code": fixed.strip(),
            "explanation": "Replaced weak crypto primitive with stronger hashlib.sha256.",
            "imports_needed": [],
        }

    def _fix_long_method(
        self, issue: Dict[str, Any], code: str
    ) -> Dict[str, Any]:
        """Suggest extracting sub-functions from long methods."""
        snippet = issue.get("code", "")
        line = issue.get("line", 0)

        return {
            "smell_type": "long_method",
            "line": line,
            "original_code": snippet.strip()[:200],
            "fixed_code": None,
            "explanation": (
                "This method is too long. Apply 'Extract Method' refactoring:\n"
                "1. Identify groups of related statements\n"
                "2. Move each group into its own named function\n"
                "3. Replace the group with a function call\n"
                "Example: step1 = validate(data); step2 = transform(step1) "
                "→ create validate() and transform() as separate functions."
            ),
            "imports_needed": [],
        }

    def _fix_god_object(
        self, issue: Dict[str, Any], code: str
    ) -> Dict[str, Any]:
        """Suggest splitting god objects into focused classes."""
        snippet = issue.get("code", "")
        line = issue.get("line", 0)

        return {
            "smell_type": "god_object",
            "line": line,
            "original_code": snippet.strip()[:200],
            "fixed_code": None,
            "explanation": (
                "This class has too many responsibilities. Apply the "
                "Single Responsibility Principle:\n"
                "1. Group related methods by functionality (auth, db, email, etc.)\n"
                "2. Create separate classes for each group\n"
                "3. Use composition: the main class holds references to helpers\n"
                "Example: class AppManager → class AuthService + class DBService + class EmailService"
            ),
            "imports_needed": [],
        }

    def _fix_deep_nesting(
        self, issue: Dict[str, Any], code: str
    ) -> Dict[str, Any]:
        return {
            "smell_type": "deep_nesting",
            "line": issue.get("line", 0),
            "original_code": issue.get("code", "").strip(),
            "fixed_code": None,
            "explanation": "Reduce nesting using guard clauses or by extracting nested blocks into helper functions.",
            "imports_needed": [],
        }

    def _fix_unused_variables(
        self, issue: Dict[str, Any], code: str
    ) -> Dict[str, Any]:
        snippet = issue.get("code", "")
        line = issue.get("line", 0)

        # Conservative fix: comment out the unused assignment for manual review.
        fixed = f"# TODO: removed unused assignment\n# {snippet.strip()}"
        return {
            "smell_type": "unused_variables",
            "line": line,
            "original_code": snippet.strip(),
            "fixed_code": fixed,
            "explanation": "Marked unused variable assignment for removal.",
            "imports_needed": [],
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _no_fix(self, issue: Dict[str, Any], explanation: str) -> Dict[str, Any]:
        return {
            "smell_type": issue.get("type", ""),
            "line": issue.get("line", 0),
            "original_code": issue.get("code", "").strip(),
            "fixed_code": None,
            "explanation": explanation,
            "imports_needed": [],
        }
