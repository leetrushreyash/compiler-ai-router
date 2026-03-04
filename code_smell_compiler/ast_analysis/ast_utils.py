import ast
from typing import List, Tuple, Dict

def get_function_nodes(tree: ast.AST) -> List[ast.FunctionDef]:
    return [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]


def get_class_nodes(tree: ast.AST) -> List[ast.ClassDef]:
    return [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]

def function_length(node: ast.FunctionDef) -> int:
    if hasattr(node, 'body') and node.body:
        first = node.body[0].lineno
        last = node.body[-1].lineno
        return max(0, last - first + 1)
    return 0


def class_length(node: ast.ClassDef) -> int:
    if hasattr(node, 'body') and node.body:
        first = node.body[0].lineno
        last = node.body[-1].lineno
        return max(0, last - first + 1)
    return 0

def max_nesting(node: ast.AST) -> int:
    max_depth = 0

    def visit(n, depth=0):
        nonlocal max_depth
        if isinstance(n, (ast.If, ast.For, ast.While, ast.Try, ast.With, ast.AsyncFor)):
            depth += 1
            max_depth = max(max_depth, depth)
        for child in ast.iter_child_nodes(n):
            visit(child, depth)

    visit(node, 0)
    return max_depth

def count_nested_loops(node: ast.AST) -> int:
    count = 0

    def visit(n, loop_depth=0):
        nonlocal count
        if isinstance(n, (ast.For, ast.While, ast.AsyncFor)):
            loop_depth += 1
            if loop_depth > 1:
                count += 1
        for child in ast.iter_child_nodes(n):
            visit(child, loop_depth)

    visit(node, 0)
    return count

def find_nested_loop_lines(node: ast.AST) -> List[int]:
    lines: List[int] = []

    def visit(n, loop_depth=0):
        if isinstance(n, (ast.For, ast.While, ast.AsyncFor)):
            loop_depth += 1
            if loop_depth > 1:
                lines.append(getattr(n, 'lineno', -1))
        for child in ast.iter_child_nodes(n):
            visit(child, loop_depth)

    visit(node, 0)
    return lines

def uses_eval_exec(tree: ast.AST) -> List[Tuple[int, str]]:
    occurrences = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in ("eval", "exec"):
            lineno = getattr(n, 'lineno', -1)
            occurrences.append((lineno, n.func.id))
    return occurrences

def find_hardcoded_secrets(tree: ast.AST) -> List[Tuple[int, str]]:
    findings = []
    keywords = ("password", "secret", "api_key", "token", "passwd")
    for n in ast.walk(tree):
        if isinstance(n, ast.Assign):
            for target in n.targets:
                if isinstance(target, ast.Name) and isinstance(n.value, ast.Constant) and isinstance(n.value.value, str):
                    val = n.value.value.lower()
                    if any(k in target.id.lower() for k in keywords) or any(k in val for k in keywords):
                        findings.append((getattr(n, 'lineno', -1), getattr(target, 'id', '<unknown>')))
    return findings

def find_exception_swallowing(tree: ast.AST) -> List[int]:
    lines = []
    for n in ast.walk(tree):
        if isinstance(n, ast.ExceptHandler):
            # check for bare pass or empty body
            body = getattr(n, 'body', [])
            if not body:
                lines.append(getattr(n, 'lineno', -1))
            else:
                if len(body) == 1 and isinstance(body[0], ast.Pass):
                    lines.append(getattr(n, 'lineno', -1))
    return lines

def detect_duplicate_functions(tree: ast.AST) -> List[Tuple[int, int]]:
    dumps: Dict[str, int] = {}
    duplicates: List[Tuple[int, int]] = []
    for f in get_function_nodes(tree):
        # ast.dump expects an AST node; f.body is a list, so wrap into a Module
        try:
            mod = ast.Module(body=f.body, type_ignores=[])
            sig = ast.dump(mod)
        except Exception:
            sig = ast.dump(f)
        if sig in dumps:
            duplicates.append((getattr(f, 'lineno', -1), dumps[sig]))
        else:
            dumps[sig] = getattr(f, 'lineno', -1)
    return duplicates


def get_method_nodes(cls: ast.ClassDef) -> List[ast.FunctionDef]:
    return [n for n in cls.body if isinstance(n, ast.FunctionDef)]


def class_method_count(cls: ast.ClassDef) -> int:
    return len(get_method_nodes(cls))


def class_attribute_count(cls: ast.ClassDef) -> int:
    names = set()
    for node in ast.walk(cls):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == "self":
                    names.add(target.attr)
                elif isinstance(target, ast.Name):
                    names.add(target.id)
    return len(names)


def method_attribute_access_profile(fn: ast.FunctionDef) -> Tuple[int, int]:
    self_attrs = 0
    foreign_attrs = 0
    for node in ast.walk(fn):
        if isinstance(node, ast.Attribute):
            if isinstance(node.value, ast.Name):
                if node.value.id == "self":
                    self_attrs += 1
                else:
                    foreign_attrs += 1
            elif isinstance(node.value, ast.Attribute):
                foreign_attrs += 1
    return self_attrs, foreign_attrs
